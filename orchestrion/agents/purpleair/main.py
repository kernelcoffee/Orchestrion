import requests
import logging
import operator

logger = logging.getLogger(__name__)

AVAILABILITY_URL = "https://www.purpleair.com/json?show="


class ServiceModule:
    def __init__(self, config, output):
        self.interval = int(config["interval"])
        self.output = output
        self.sensors = [item.strip() for item in config["sensors"].split(",")]

    def _format_output(self, json):
        return {
                "measurement": "purpleair",
                "tags": {"location": json["Label"], "sensor": json["ID"]},
                "time": json["LastSeen"] * 1000000000,
                "fields": {
                    "pm2_5": float(json["pm2_5_cf_1"]),
                    "pm1_0": float(json["pm1_0_cf_1"]),
                    "pm10_0": float(json["pm10_0_cf_1"]),
                },
            }
    def run(self):
        # for sensor_id in self.sensors:
        query = requests.get(f"https://www.purpleair.com/json?show={'|'.join(self.sensors)}")
        query.raise_for_status()
        json = query.json()

        results = []
        for result in json["results"]:
            logger.debug(result)
            results.append(self._format_output(result))
        self.output(results)
