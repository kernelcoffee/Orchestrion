import speedtest

class ServiceModule:
    def __init__(self, config, output):
        self.interval = int(config["interval"])
        self.write = output
        self.speedtester = speedtest.Speedtest()
        self.speedtester.get_best_server()

    def _format_output(self, download, upload):
        return [{
                "measurement": "speedtest",
                "fields": {
                    "download": download,
                    "upload": upload,
                },
        }]

    def run(self):
        download = self.speedtester.download()
        upload = self.speedtester.upload()
        self.write(self._format_output(download, upload))