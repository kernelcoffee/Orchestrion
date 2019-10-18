from importlib import import_module

import logging
import configparser
import schedule
import time

config = configparser.ConfigParser()
config.read("config.ini")

for module in config.sections():
    if config[module].getboolean("active"):
        loaded_module = getattr(import_module(f"modules.{module}.main"), "ServiceModule")(config[module])
        schedule.every(loaded_module.interval).minutes.do(loaded_module.run)
        
while True:
    schedule.run_pending()
    time.sleep(1)
