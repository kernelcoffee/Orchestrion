import requests
import logging
import json
import ipaddress

logger = logging.getLogger(__name__)

API_URL = "https://dns.api.gandi.net/api/v5"


class ServiceModule:
    def __init__(self, config, output):
        self.interval = int(config["interval"])
        self.write = output
        self.api_secret = config["api_secret"]
        self.domain = config["domain"]
        self.subdomains = [item.strip() for item in config["subdomains"].split(",")]
        self.public_ip = None
        self.ttl = 300

    def _get_public_ip(self):
        return requests.get("https://api.ipify.org").text

    def _get_dns_ip(self, domain_uuid, subdomain):
        url = f"{API_URL}/zones/{domain_uuid}/records/{subdomain}/A"
        headers = {"X-Api-Key": self.api_secret}

        res = requests.get(url, headers=headers)
        json_object = json.loads(res._content)
        if res.status_code == 200:
            return json_object["rrset_values"][0]

        logger.error(
            f"Error: HTTP Status Code {res.status_code} when trying to get IP from subdomain {subdomain} : {json_object['message']}"
        )
        return False

    def _get_uuid(self):
        url = f"{API_URL}/domains/{self.domain}"
        u = requests.get(url, headers={"X-Api-Key": self.api_secret})
        json_object = json.loads(u._content)
        if u.status_code == 200:
            return json_object["zone_uuid"]

        logger.error(f"Error: HTTP Status Code {u.status_code} when trying to get Zone UUID")
        return False

    def _update_records(self, uuid, subdomain, ip):
        url = f"{API_URL}/zones/{uuid}/records/{subdomain}/A"
        payload = {"rrset_ttl": self.ttl, "rrset_values": [ip]}
        headers = {"Content-Type": "application/json", "X-Api-Key": self.api_secret}
        res = requests.put(url, data=json.dumps(payload), headers=headers)
        json_object = json.loads(res._content)

        if res.status_code == 201:
            # print(f"Status Code: {u.status_code} {json_object['message']} IP updated for {subdomain}"
            return True
        # logger.error(f"Error: HTTP Status Code {u.status_code} when trying to update IP from subdomain {subdomain}"
        return False

    def _format_output(self, js):
        return [
            {"measurement": "gandi_dynamic_dns", "fields": {"ip": js["ip"], "subdomain_updated": js["counter"]}},
        ]

    def run(self):
        # Get public IP
        try:
            public_ip = self._get_public_ip()
            ipaddress.ip_address(public_ip)
        except Exception as e:
            logger.error(f"Could not retrieve public IP : {e}")
            return

        # Check if public ip from last check changed
        if public_ip == self.public_ip:
            # Our public ip didn't change, nothing to do
            return

        logger.info(f"Public IP has changed: {public_ip} -> {self.public_ip}")

        # Get UUID of domain name to interact with
        self.domain_uuid = self._get_uuid()
        if not self.domain_uuid:
            return

        output = {"ip": public_ip}
        counter = 0
        for subdomain in self.subdomains:
            logger.info(f"Checking for {subdomain}.{self.domain}")
            if public_ip != self._get_dns_ip(self.domain_uuid, subdomain):
                logger.info(f"IP on DNS record for subdomain {subdomain} doesn't match current public ip")
                self._update_records(self.domain_uuid, subdomain, public_ip)
                counter += 1

        output["counter"] = counter

        # Saving new public ip
        self.public_ip = public_ip
        self.write(self._format_output(output))
