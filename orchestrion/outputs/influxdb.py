import logging
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError, InfluxDBServerError

logger = logging.getLogger(__name__)


class InfluxClient:
    def __init__(self, config):
        logger.info("Create InfluxDB client with:")
        self.address = str(config.get("Address", fallback="localhost"))
        self.port = config.getint("Port", fallback=8086)

        logger.debug(f"InfluxDB client connection to {self.address}:{self.port}")

        self.client = InfluxDBClient(
            self.address,
            self.port,
            username=config.get("Username", fallback=""),
            password=config.get("Password", fallback=""),
            database=config.get("Database", fallback="orchestrion"),
            ssl=config.getboolean("SSL", fallback=False),
            verify_ssl=config.getboolean("Verify_SSL", fallback=True),
        )

    def write(self, data):
        try:
            logger.debug(f"Writing to influxdb {data}")
            self.client.write_points(data)
        except (InfluxDBClientError, ConnectionError, InfluxDBServerError) as e:
            if hasattr(e, "code") and e.code == 404:
                logger.info(e)
                self.client.create_database(config.get("Database", fallback="orchestrion"))
                self.client.write_points(data)
            else:
                logger.debug(f"Error writing to influx {e}")
