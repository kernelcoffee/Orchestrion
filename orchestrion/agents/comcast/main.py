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

        # data = {
        #     "user": self.username,
        #     "passwd": self.password,
        #     "reqId": req_id,
        #     "deviceAuthn": "false",
        #     "s": "oauth",
        #     "forceAuthn": "1",
        #     "selectAccount": "false",
        #     "r": "comcast.net",
        #     "rm": "1",
        #     "ipAddrAuthn": "false",
        #     "continue": URL_AUTHORIZE,
        #     "passive": "false",
        #     "lang": "en",
        #     "client_id": "my-account-web",
        #     "selectAccount": "false",
        # }

        data=f"user={self.username}&passwd={self.password}&rm=1&r=comcast.net&selectAccount=false&s=oauth&deviceAuthn=false&continue=https%3A%2F%2Foauth.xfinity.com%2Foauth%2Fauthorize%3Fclient_id%3Dmy-account-web%26prompt%3Dlogin%26redirect_uri%3Dhttps%253A%252F%252Fcustomer.xfinity.com%252Foauth%252Fcallback%26response_type%3Dcode%26state%3Dhttps%253A%252F%252Fcustomer.xfinity.com%252F%2523%252Fdevices%26response%3D1&ipAddrAuthn=false&forceAuthn=1&lang=en&passive=false&client_id=my-account-web&reqId={req_id}&X-hzfdeCEGvt-f=A05ZfoB0AQAAdYdujFZ6NuE5cLJQt2Uc2xMh3TEBsBlvZfUCrXnKnSehLCopARgFlVmcuBShwH8AAB71AAAAAA%3D%3D&X-hzfdeCEGvt-b=-qgfj1y&X-hzfdeCEGvt-c=AxDMe4B0AQAAgh-5wBz5eYEGcwrkIvj-Sr8TMOI38wi0YtIUg6j41o-6VlijAa4Vc9GucrtWwH8AAOfvAAAAAA%3D%3D&X-hzfdeCEGvt-d=o_0&X-hzfdeCEGvt-z=p&X-hzfdeCEGvt-a=jzLj5Wyv8Iww9Gxar5EwYafgDPeyB8mDOlIsJZ5oOFf2JDf5M4E8V%3DahuJ2bfBtGa9a4_5op4gep2cP64Ly_mwBGjNVgjqYGhakB_emOfn6RO1m2ZI0dEhJmD0dgHwRcJi4bJKbYu_wzdX_8yPlhxXjVBdMkTXHfUTb2cVxtkT9m9YvSJR5n0RCoXopANPt7u412XHHTXx_HRYIepmx7B3gcCMYauf3mV0G2yKbdnoBkcJE78o7bsxJHUlUpCUiWZ0Kkcyqsul4DueqbvN5bAwYhyZSOJfqxCuVHhF_TjrvCsUbDPbRt60EKSd1KnCUDrM9J0i8iZl8YqlGfXm6aNDPeN1luZ70T548lzlKAuDiHQdohLwG9ID5SupS6q80gjM3P9B8M7vM2%3DUSVb3zrfJKk1I0Z_Zpr6kuH9ZYiFSpxM5_snRExkk69zUEoM73W8gBvkrhoxA5fB2IpxIbkvU9RimS%3D8_4bCFWWhZEVJQDFisd8ERqO9D3sTptifQEV_hWMEhPV6G9iSxTsF9AU2tCSqmEEh8uNiq3frH%3D2HDOsKG1ICWzA4aFUAwMKoJrigX2dLJqwctVsN7%3DcEJ8qXk%3DlC_9D6BiVKZ5kkXeKicnACcqMa%3DV3jiI3cb6cIEodjQb2sobiJH6YJQ0JnB0b0lBcHssTyrAvbFk0Oruvfn2t0nf%3DoBQa2PS5X5DM14lpuGYKU7Wx4SPaaChJdgt%3DEejPwHCtYr_ZOQjV%3DHYXswVvOaubrnqyOugqZFyZrvBoFH3cb%3DTVpBD_Jk5UofxVcCUKQOkfjCOSFZtd1lJLFnkNfZidx4gLweNgMqi9n8Ti3TOjTl9qUzCYS7ql%3D1jlsyB%3DmjRyjpIFVc6MpvR90NYi94%3DTBfLXKR7itBxAgcwbs%3Do_IAprmEZYmzY0Fc8KUn_kdj8xaZqufB5IIyZKFkrhDioJ563BH_PndqYu24z3e9fG0V4lNigvzxcuEHr90UZSeENWFJ9a45HpO4upek54S7DB4yqmOnBsdAwl8Of7lsz0MHFGPIz1AuTbcjdVxiaiMzFDu_be2jMSTLeUjrt1dAu9ZZ6NP62hHXS0j1EGsC9POPO_RV%3DiY0aXnuAvGWV5Yp3qMx5i23Q7dh%3DQZuuXp%3DkzVkNk_RG8n6au9TBfYY1kY06c7TKAYxYdGcvvkzfgBKTXYC3pmhT256hN7%3DNqW%3DtL7c5oyPPYSgUi2mw5raxxuHmmgYOTf%3DyLT4a36SspTkEpI5Bv4ZjpzMlNXJI3bq%3D8N9N%3DcwvtuRzMN%3DCQ2x%3DRC8V3PhtMb29GfxsuPddfRWOOsNoANi%3DyGdVvkH8pjXa43yz7ifFbpIZiUGvrZKbmsx%3Dk%3DPvEtzeqdMq691rTB7I3y6BB6Fo%3DPeH%3DcXEa53kz%3DhdXKXJ7JsHBQYLX%3D%3D5z4csHAmRL4hBFTWeQsWvuSUQsKOtaYNmLdfyjZujQuWNV7LwUQGSUjEkVfG9Y6PQrQa7X1r2m3ABuGn4L42DdVcEgBV6VbqtOBt_OrjGJi0g9ijVAfA4NTDHxz11DBtP%3DRUxO3sWRF_NxRy7FoHwV1eEwh6aqlz_bJCI4nfxvYWk7s49eE6sFyCAdLv2ZXLAXm_7rrFbLcEAt5Kl5cP18xb5pMYrECS56wQ8VYCipzGzJF1VmdaA0c2bRDWwFkUyH9zgZAG0h3_DXb1EX28UScUxJ%3DYnQaZNlh_cYkuLmWXgMXno9EpGyhhwrOj5WpVLsAbuD9pmeJetDX5Ic3H_el4uIAJuKhf%3DXKVo3s_ylv7h7RfMgsZDHxRIC6VTeaj5ZcXqz7gECMwRaH7pLZGlRn4hOtIbi3AMfK%3DkF4L1FZXDTxNoDMtMiNyohSCfF2gY7L9qeO0thg98DlBhrATSfRd7ToLc_k3PqGEG1jqMVE6OODnyUU8jOEio1G%3DkFadGCqhtg7cfgMKCZ1_j8kmNPY07aLoIzWkTA0Z%3DBw2FyTM_GEkJZo3Z6ah63RivCInoBZISc1OBwiK2aW0cFf8Pifr2M0okYBQqCQORRP23BuWDOx42owYkSZ5Knk6qf_DFPyhhcwDiauQzfI41zXDB2MilagE4jifyLvv9sK0rSaRQjf7ih9fzxj2wiJmJdemWqk4585Lbg5iX2Y2OwkV6_nVsW2RU4eecpZP6Fc2dlNL9s8POCamTDiAElX_nWvXbESpRf4ArAYPIMDPCTVgI44tTiO4d7ZA_hN6ZmmKoz7GusoNzKIlymFKv7355J3jta6%3DgXXo750iAFOjRNmfWUxZsu1fXIB9S80yZqd9eiOu62egwWqf1jY8Mye7yGbl6avkkwkwC4W6kuAxxGcgRdwCGQjxF9L%3DfTfPP1w%3DAvc1OdThF0saZ1DN8utjq2WNf36J8x9Y0Lr4Ge6JfnyOPBsFeiCyUKLmyNkI0CsqB_BR06j0GtARUms_FYBRQNEKDTeIUkMJZ7CpRznKRIvGWEwWPxPO2urOnuKCYXOa%3DrwTn1Dw7sLcpGuE1_Tjiq1BDtZVmF8ZeksWmeLqiDlf0fBNidwYuXCz_UpKrYIl2KMcpXyzA2rGTv50XiwIjh4NdcTRk3%3DeT85iRImDyTDFEGRrmb7dSbZTHiW2hsx2aZh77RTch9mmViTn5mLsvXx_9HWTnhi8hxJagyulTBU8uPWJzrNSCiipkWVczZRqqw40WuKTcOnQdCW5P8cIm2xVKKkKUQbIhYlMt_3rNa9tEVf2JMrCYvIhe7Iz_9gD_TSjjb5GNQf5OsdldZfSOHzAb3j_1y7lqSEc1bxPQeWNf%3Dy5garaBIceX6cQ92s2BVL9BJfPK4pXbKL_hAoHdEA6i%3D6aTo4y2Ih0N_mdSd_T9cPtttJQDYr1FCdzUEIaUjSD5DfcWDpSDyBHR3_1HftAJ%3DfH_Oni3cGMvYZdc1u3DmA4IYPygKt8JjrP2mr2YjzS6QVOlH3c8ASOVwNI%3D_gFc4twErGlKWTSQ%3D0gkbwjpW2_N_DGsX%3DW7XDV92FoeY6ZWWCNdrmdd5oiFpWXqwKiWnYf%3D_CPe7bV4wszn%3DiKO0eINGuNXu0rgMzyG5bnO5yVNT9LHEy885Ibwe1CLMMUuw15yaZO%3Dz9jRsfu4ClBWbNe%3D0Q5l69GYX72CGfNkrPYiq06AD6%3Dhx9AuB328QywBD58rFfs691V9GH_1e8mTRHUqybxQK7xgdD160syMWcLB0HGx5C4vlLuzCkMLQgED7L5n4QOiHpsP7cbSChmZU6UGq06bddkSdEEF9qKIC9EXQoqCEXyO_lpudQu60EMZmXCAh4N9LVQzqzQksnoIJxNDkdLczVsLRupqys0Dm906n3HKwJuD64Ek6Z8jFqvYho2eyWZ_w4T8ysmb0dFXfUX%3DqVaeKGeAkrW1p8tbFxwMo0IyajuLE32h3Hm3D8eMzEuuiCYsev%3DC3A_RnKphuRyP5nxWc1DMfKX77L6q0uCmMSpXySl35GGVgjJXIrH3JzZijWvzb91vJMCJ3QJIS%3DJ0%3DleaI3Pra2vilciLKHsjsTmIkYqUY%3DKJ59eYz6BXSu302tLIS6wFB0zD1VgjnBKjFY2Mfq_TGVOfpz6yEtcw55bbuJ0h_xSGGCoW8Bz%3DX0i75Ykd2zIwfhK6NHq4UMdp8z1Fgh3S9fcNrFR01MpeZVxCFkybktghKg73ajNjfLY%3DqVQLO9YSg%3DRGxQgC9rO5Wasdj5tA80jBFzTMF_FGMicPkUpH12iJmTk%3Dyz28u3cPFfy0_r0KEfLJFqjTEAxhy_lw6CJFWq8SdHgKewFZwWVujUUQTBMjUzNhXa%3Dg9PEvHx7PGYbfrpc65db8SOUoOdgiHADUDTWXr5s3bZUt8%3D35j1CxFqqh2ss6HnlfUryIg1tX7bBvGsC3a%3DjTkLGxJtHdO14aARZR7xJQF54rJ_cz_wPAQYFnEitsknyZZUPngoU%3DVQO%3Df8OnDUZyuSeJgdcWCIaCCrRlRW_XK1I5PO4vB1HqK8ZY5e0gBsWIvMk5ttZ6VUTLOtG5BCIKlVr1hux29bxYAY6uXgRk1YRnk7aIZsMw"
        logger.debug("Posting to login...")
        res = self.session.post(URL_LOGIN, data=data)

        if self._is_security_check(res):
            logger.warning("Security check found! Please bypass online and try this again.")
            return

        if res.status_code == 200:
            logger.info("Login sucessful")
        else:
            logger.info("Login failed")

        logger.debug(res.content)

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
            print(res.status_code, res.text)
            if res.status_code == 401:
                logger.info("Session is not authorized, attempting to login")
                self._login()
            if res.status_code == 200:
                self.output(self._format_output(json.loads(res.text)))
