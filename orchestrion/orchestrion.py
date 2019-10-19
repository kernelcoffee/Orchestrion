from importlib import import_module

import logging
import configparser
import argparse
import pathlib

import schedule
import time

logger = logging.getLogger(__name__)
config_path = "config.ini"

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
if args.debug:
    logging.basicConfig(level=logging.DEBUG)

# CONFIG PATH
if args.config and args.config.exists():
    config_path = args.config

config = configparser.ConfigParser()
config.read(config_path)

for module in config.sections():
    if config[module].getboolean("active"):
        loaded_module = getattr(import_module(f"modules.{module}.main"), "ServiceModule")(config[module])
        interval = loaded_module.interval if args.interval is None else args.interval
        schedule.every(interval).minutes.do(loaded_module.run)

while True:
    schedule.run_pending()
    time.sleep(1)
