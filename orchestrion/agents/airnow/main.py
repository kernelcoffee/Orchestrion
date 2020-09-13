import requests
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

AIRNOW_URL = "https://airnowgovapi.com/reportingarea/get"


class ServiceModule:
    def __init__(self, config, output):
        self.interval = int(config["interval"])
        self.output = output
        self.last_report = dict()
        self.payload = {
            "latitude": config["latitude"],
            "longitude": config["longitude"],
            "stateCode": config["stateCode"],
            "maxDistance": config["maxDistance"],
        }

    def _format_output(self, js, report_date: int):
        return [
            {
                "measurement": js["parameter"],
                "tags": {"location": js["reportingArea"], "stateCode": js["stateCode"],},
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
        res = requests.post(AIRNOW_URL, data=self.payload)
        if res.status_code == 200:
            logger.debug(res.json())
            for entry in res.json():
                if entry["issueDate"] and entry["time"]:
                    report_date = entry["issueDate"] + "-" + entry["time"]
                    logger.debug(entry)
                    report_date = int(datetime.strptime(report_date, "%m/%d/%y-%H:%M").timestamp())
                    data = self._format_output(entry, report_date)

                    if (
                        entry["parameter"] not in self.last_report
                        or self.last_report[entry["parameter"]] != report_date
                        and self.last_report[entry["parameter"]] < report_date
                    ):
                        self.last_report[entry["parameter"]] = report_date
                        logger.info(data)
                        self.output(data)
