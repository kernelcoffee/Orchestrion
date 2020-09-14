import requests
import logging
import pytz
from datetime import datetime

logger = logging.getLogger(__name__)


class ServiceModule:
    def __init__(self, config, output):
        self.interval = int(config["interval"])
        self.output = output
        self.last_report = dict()
        self.latitude = config["latitude"]
        self.longitude = config["longitude"]
        self.stateCode = config["stateCode"]
        self.postcode = config["postcode"]
        self.maxdistance = config["maxdistance"]
        self.api_key = config["api_key"]

    def _format_output(self, json, report_date: int):
        return [
            {
                "measurement": json["ParameterName"],
                "tags": {"location": json["ReportingArea"], "postcode": self.postcode},
                "time": report_date,
                "fields": {
                    "aqi": json["AQI"],
                    "zone": json["Category"]["Number"],
                    "libelle": json["Category"]["Name"],
                },
            }
        ]

    def run(self):
        try:
            res = requests.post(
                f"http://www.airnowapi.org/aq/observation/latLong/current/?format=application/json&latitude={self.latitude}&longitude={self.longitude}&distance={self.maxdistance}&API_KEY={self.api_key}"
            )
        except Exception as e:
            logger.error(str(e))
            return

        if res.status_code != 200:
            logger.error(res.content)
            return

        for entry in res.json():
            report_date = pytz.timezone("US/Pacific").localize(
                datetime.strptime(entry["DateObserved"].strip(), "%Y-%m-%d").replace(hour=entry["HourObserved"])
            )
            report_date = int(report_date.astimezone(pytz.utc).timestamp()) * 1000000000

            if (
                entry["ParameterName"] not in self.last_report
                or self.last_report[entry["ParameterName"]] != report_date
                and self.last_report[entry["ParameterName"]] < report_date
            ):
                self.last_report[entry["ParameterName"]] = report_date
                self.output(self._format_output(entry, report_date))
