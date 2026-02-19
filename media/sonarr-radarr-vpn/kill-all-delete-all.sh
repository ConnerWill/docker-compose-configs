#!/usr/bin/env bash

set -e

ENV_FILE="./.env"
PROG="${BASH_SOURCE[0]}"
INPUT="${1}"

show_help(){
  cat <<EOF
Usage: ${PROG} YES

EOF
exit 1
}


show_status(){
  printf "Starting removal\n"
}

if [[ -z "${INPUT}" ]]; then
  show_help
elif [[ "${INPUT}" == "YES" ]]; then
  show_status
else
  show_help
fi

source "${ENV_FILE}" || exit 1

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


