#!/usr/bin/env bash

ENV_FILE="./.env"

source "${ENV_FILE}" || return 1

docker-compose kill
docker container rm gluetun qbittorrent radarr sonarr
docker image rm gluetun
docker image rm qbittorrent
docker image rm radarr
docker image rm sonarr
docker network rm sonarr-radarr-docker-compose_default
docker volume rm sonarr-radarr-docker-compose_gluetun
docker volume rm sonarr-radarr-docker-compose_qbittorrent_config
docker volume rm sonarr-radarr-docker-compose_radarr_config
docker volume rm sonarr-radarr-docker-compose_sonarr_config


