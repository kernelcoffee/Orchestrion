[![GPLv3 license](https://img.shields.io/badge/License-GPLv3-blue.svg)](http://perso.crans.org/besson/LICENSE.html)

# Orchestrion
Orchestrion is a Agent launcher that is designed to load and start agent at regular interval and send the result to a database

### Current modules
- Comcast: Get current datacap and courtesy
- Speedtest: Get download, upload and ping
- Gandi: Dynamic DNS updater for the Gandi registar

## Setup
```bash
virtualenv -p python3 env
source env/bin/activate
pip3 install -r requirements/common.txt
```

## Configuration
First create your config file

```
cp config.ini.sample config.ini
```

in order to enable the modules, you need to copy their configuration section into your config.ini file

example:
```bash
# Configuration file
[influxdb]
Address=localhost
Port=8086
Username=
Password=
Database=orchestrion

[comcast]
interval=30
username=<username>
password=<password>

[speedtest]
interval=30
```

## Usage
```bash
python orchestrion/orchestrion.py -c <path_to_config.ini>
```

## Docker

Build & run Docker image
```bash
docker build -t orchestion .
docker run -d -v /path/to/config/folder:/config --name orchestrion orchestrion

```

docker hub
```
docker run -d -e DEBUG="true" -v /path/to/config/folder:/config --name orchestrion kernelcoffee/orchestrion
```

docker-compose
```
  orchestrion:
    container_name: orchestrion
    image: kernelcoffee/orchestrion
    environment:
      DEBUG: "true"
    volumes:
      - /path/to/config/folder:/config

```