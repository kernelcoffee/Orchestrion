from importlib import import_module

import os
import logging
import configparser
import argparse
import pathlib

import schedule
import time

from outputs import influxdb

logger = logging.getLogger(__name__)
config = configparser.ConfigParser()
config_path = "config.ini"

# Init options
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="Increase verbosity of output", action="store_true")
parser.add_argument("-d", "--debug", help="Enable debug mode", action="store_true")
parser.add_argument("-c", "--config", help="Path of the config file", type=pathlib.Path)
parser.add_argument("-i", "--interval", help="Override interval time", type=int)
args = parser.parse_args()

# VERBOSE
if args.verbose:
    logging.basicConfig(level=logging.INFO)

# DEBUG
if args.debug or os.environ.get("DEBUG"):
    logging.basicConfig(level=logging.DEBUG)

# CONFIG PATH
if args.config and args.config.exists():
    config_path = args.config

config.read(config_path)

# Init influx
influx_config = config["influxdb"]
influxclient = influxdb.InfluxClient(influx_config)
config.remove_section("influxdb")

for module in config.sections():
    logger.info(f"Loading module {module}")
    loaded_module = getattr(import_module(f"agents.{module}.main"), "ServiceModule")(
        config[module], influxclient.write
    )
    interval = loaded_module.interval if args.interval is None else args.interval
    schedule.every(interval).minutes.do(loaded_module.run)

schedule.run_all()
while True:
    schedule.run_pending()
    time.sleep(1)
