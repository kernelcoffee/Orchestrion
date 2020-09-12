import requests
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

AIRNOW_URL = "https://airnowgovapi.com/reportingarea/get"


class ServiceModule:
    def __init__(self, config, output):
        self.interval = int(config["interval"])
        self.latitude = config["latitude"]
        self.longitude = config["longitude"]
        self.stateCode = config["stateCode"]
        self.maxDistance = config["maxDistance"]
        self.output = output
        self.last_report = dict()

    def _format_output(self, js, report_date: int):
        return [
            {
                "measurement": js["parameter"],
                "tags": {
                    "location": js["reportingArea"],
                    "stateCode": js["stateCode"],
                },
                "time": report_date * 1000000000,
                "fields": {
                    "aqi": js["aqi"],
                    "category": js["category"],
                    "isActionDay": js["isActionDay"],
                    "discussion": js["discussion"],
                },
            }
        ]

    def run(self):
        data = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "stateCode": self.stateCode,
            "maxDistance": self.maxDistance,
        }

        res = requests.post(AIRNOW_URL, data=data)
        if res.status_code == 200:
            entry = res.json()[0]
            report_date = entry["issueDate"] + "-" + entry["time"]
            report_date = int(datetime.strptime(report_date, "%m/%d/%y-%H:%M").timestamp())
            data = self._format_output(entry, report_date)

            if entry["parameter"] not in self.last_report or self.last_report[entry["parameter"]] != report_date:
                self.last_report[entry["parameter"]] = report_date
                logger.debug(data)
                self.output(data)