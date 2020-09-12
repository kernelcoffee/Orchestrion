import requests
import logging
import functools
import operator

from .servers_utils import ServerUtils

logger = logging.getLogger(__name__)

AVAILABILITY_URL = "https://www.ovh.com/engine/api/dedicated/server/availabilities?country=world"


class ServiceModule:
    def __init__(self, config, output):
        self.utils = ServerUtils()
        self.interval = int(config["interval"])
        self.write = output
        self.wanted = [item.strip() for item in config["servers"].split(",")]
        self.wanted_references = functools.reduce(
            operator.iconcat, [self.utils.name_to_reference(name) for name in self.wanted], []
        )

    def _get_data(self):
        try:
            r = requests.get(AVAILABILITY_URL)
            if r.status_code == 200:
                return r.json()
        except requests.RequestException:
            logger.error("Unable to connect to OVH")
        except (ValueError, KeyError):
            logger.error("Invalid response from OVH")

    def _process_data(self, data):
        result = {}
        for server in self.wanted_references:
            result[server] = {}

        for server in data:
            if server["hardware"] in self.wanted_references:
                for datacenter in server["datacenters"]:
                    if server["region"] in result[server["hardware"]].keys():
                        continue
                    if datacenter["availability"] not in ("unavailable", "unknown"):
                        result[server["hardware"]][server["region"]] = datacenter["availability"]
        return result

    def _format_output(self, js):
        fields = {}
        for ref in js:
            for location in js[ref]:
                print(self.utils.reference_to_name(ref), ref, location, js[ref][location])

    def run(self):
        data = self._get_data()
        result = self._process_data(data)
        self._format_output(result)
