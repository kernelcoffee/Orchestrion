FROM python:3.7-alpine

# set version label
ARG BUILD_DATE
ARG VERSION
ARG ORCHASTRION_RELEASE
LABEL build_version="Linuxserver.io version:- ${VERSION} Build-date:- ${BUILD_DATE}"

COPY orchestrion/ /app
COPY requirements/common.txt /app/requirements.txt

WORKDIR /app


RUN pip3 install -r requirements.txt

RUN mkdir /config
VOLUME /config

CMD [ "python3", "/app/orchestrion.py", "-c", "/config/config.ini"]
