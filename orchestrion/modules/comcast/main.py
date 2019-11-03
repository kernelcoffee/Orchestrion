import requests
import logging
import re
import json

from html.parser import HTMLParser

logger = logging.getLogger(__name__)

URL_OAUTH = "https://customer.xfinity.com/oauth/force_connect/?continue=%23%2Fdevices"
URL_AUTHORIZE = "https://oauth.xfinity.com/oauth/authorize?client_id=my-account-web&prompt=login&redirect_uri=https%3A%2F%2Fcustomer.xfinity.com%2Foauth%2Fcallback&response_type=code&state=%23%2Fdevices&response=1"
URL_USAGE = "https://customer.xfinity.com/apis/services/internet/usage"
URL_LOGIN = "https://login.xfinity.com/login"


class ServiceModule:
    def __init__(self, config, output):
        self.interval = int(config["interval"])
        self.username = config["username"]
        self.password = config["password"]
        self.session = requests.Session()
        self.write = output

    def _login(self):
        logger.debug("Authentication")
        res = self.session.get(URL_OAUTH)

        assert res.status_code == 200
        data = {
            x[0]: HTMLParser().unescape(x[1])
            for x in re.finditer(r'<input.*?name="(.*?)".*?value="(.*?)".*?>', res.text)
        }

        m = re.search(r'<input type="hidden" name="reqId" value="(.*?)">', res.text)
        req_id = m.group(1)
        logger.debug("Found req_id = %r", req_id)

        data = {
            "user": self.username,
            "passwd": self.password,
            "reqId": req_id,
            "deviceAuthn": "false",
            "s": "oauth",
            "forceAuthn": "1",
            "r": "comcast.net",
            "ipAddrAuthn": "false",
            "continue": URL_AUTHORIZE,
            "passive": "false",
            "client_id": "my-account-web",
            "lang": "en",
        }

        logger.debug("Posting to login...")
        res = self.session.post(URL_LOGIN, data=data)
        if res.status_code == 200:
            logger.info("Login sucessful")
        else:
            logger.info("Login failed")

    def _format_output(self, js):
        return [
            {
                "measurement": "comcast_data_usage",
                "fields": {
                    "used": js["usageMonths"][-1]["homeUsage"],
                    "total": js["usageMonths"][-1]["allowableUsage"],
                    "unit": js["usageMonths"][-1]["unitOfMeasure"],
                },
            },
            {
                "measurement": "comcast_courtersy_usage",
                "fields": {
                    "used": js["courtesyUsed"],
                    "remaining": js["courtesyRemaining"],
                    "total": js["courtesyAllowed"],
                },
            },
        ]

    def run(self):
        for attempt_number in range(3):
            logger.info("Fetching internet usage...")
            res = self.session.get(URL_USAGE)
            if res.status_code == 401:
                logger.info("Session is not authorized, attempting to login")
                self._login()
            if res.status_code == 200:
                self.write(self._format_output(json.loads(res.text)))
