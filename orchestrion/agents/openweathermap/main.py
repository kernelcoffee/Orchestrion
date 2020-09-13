import requests
import logging

logger = logging.getLogger(__name__)


class ServiceModule:
    def __init__(self, config, output):
        self.interval = int(config["interval"])
        self.output = output
        self.api_key = config["api_key"]
        self.postcode = config["postcode"]

    def _format_output(self, json):
        return [
            {
                "measurement": "weather",
                "tags": {"location": json["name"], "postcode": self.postcode},
                "time": json["dt"] * 1000000000,
                "fields": {
                    "temp": float(json["main"]["temp"]),
                    "feels_like": float(json["main"]["feels_like"]),
                    "temp_min": float(json["main"]["temp_min"]),
                    "temp_max": float(json["main"]["temp_max"]),
                    "pressure": json["main"]["pressure"],
                    "humidity": float(json["main"]["humidity"]),
                },
            }
        ]

    def run(self):
        try:
            query = requests.get(
                f"https://api.openweathermap.org/data/2.5/weather?zip={self.postcode},us&appid={self.api_key}&units=metric"
            )
        except Exception as e:
            logger.error(str(e))
            return
        self.output(self._format_output(query.json()))
