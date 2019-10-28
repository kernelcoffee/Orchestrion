import speedtest

class ServiceModule:
    def __init__(self, config, output):
        self.interval = int(config["interval"])
        self.write = output
        self.speedtester = speedtest.Speedtest()

    def _format_output(self, result):
        return [{
                "measurement": "speedtest",
                "fields": {
                    "download": result["download"],
                    "upload": result["upload"],
                    "ping": result["ping"],
                    "server_sponsor": result["server"]["sponsor"],
                    "server_city": result["server"]["name"],
                    "server_country": result["server"]["country"],
                },
        }]

    def run(self):
        self.speedtester.get_best_server()
        self.speedtester.download()
        self.speedtester.upload()
        self.write(self._format_output(self.speedtester.results.dict()))
