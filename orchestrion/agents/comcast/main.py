import requests
import logging
import re
import json
import urllib.parse 

from html.parser import HTMLParser

logger = logging.getLogger(__name__)

URL_OAUTH = "https://customer.xfinity.com/oauth/force_connect/?continue=%23%2Fdevices"
# URL_AUTHORIZE = "https://oauth.xfinity.com/oauth/authorize?response_type=code&redirect_uri=https%3A%2F%2Fauth.xfinity.com%2Foauth%2Fcallback&client_id=my-xfinity&state=https%3A%2F%2Fcustomer.xfinity.com%2F%23%2F%3FCMP%3DILC_signin_myxfinity_re&response=1"
URL_AUTHORIZE = "https://oauth.xfinity.com/oauth/authorize?client_id=my-account-web&prompt=login&redirect_uri=https%3A%2F%2Fcustomer.xfinity.com%2Foauth%2Fcallback&response_type=code&state=https%3A%2F%2Fcustomer.xfinity.com%2F%23%2Fdevices&response=1"

URL_USAGE = "https://customer.xfinity.com/apis/services/internet/usage"
URL_LOGIN = "https://login.xfinity.com/login"

OUTPUT_TYPE = "inbluxdb"


class ServiceModule:
    def __init__(self, config, output):
        self.interval = int(config["interval"])
        self.username = config["username"]
        self.password = config["password"]
        self.session = requests.Session()
        self.session.headers.update(
            {
                "user-agent": "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0",
                "Upgrade-Insecure-Request": "1",
                "content-type": "application/x-www-form-urlencoded",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9",
                "authority": "customer.xfinity.com",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                "referrer": "https://customer.xfinity.com",
            }
        )
        self.output = output

    def _is_security_check(self, res):
        # does url match?
        if res.url == "https://idm.xfinity.com/myaccount/security-check?execution=e1s1":
            return True
        # otherwise, try checking response text
        if "security-check" in res.text:
            return True
        return False

    def _login(self):
        logger.debug("Authentication")
        res = self.session.get(URL_OAUTH)

        if res.status_code != 200:
            logger.error(f"Failed to find reqId, status_code:{res.status_code}")
            return

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
            "selectAccount": "false",
            "r": "comcast.net",
            "rm": "1",
            "ipAddrAuthn": "false",
            "continue": URL_AUTHORIZE,
            "passive": "false",
            "lang": "en",
            "client_id": "my-account-web",
            "selectAccount": "false",
        }

        logger.debug("Posting to login...")
        res = self.session.post(URL_LOGIN, data=data)

        if self._is_security_check(res):
            logger.warning("Security check found! Please bypass online and try this again.")
            return

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
        for attempt_number in range(2):
            logger.info("Fetching internet usage...")
            res = self.session.get(URL_USAGE)
            logger.debug(f"result - {res.status_code} {res.content}")
            if res.status_code == 401:
                logger.info("Session is not authorized, attempting to login")
                self._login()
                continue
            if res.status_code == 200:
                logger.debug(self._format_output(json.loads(res.text)))
                self.output(self._format_output(json.loads(res.text)))
