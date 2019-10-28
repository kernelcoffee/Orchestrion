[![GPLv3 license](https://img.shields.io/badge/License-GPLv3-blue.svg)](http://perso.crans.org/besson/LICENSE.html)

# Orchestrion

Orchestrion is a Agent launcher that is designed to load and start agent at regular interval and send the result to a database


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

Build Docker image
```bash
docker build -t orchestion .
```

Run docker image
```
docker run -d -v <config_folder_path>:/config --name orchestrion orchestrion
```