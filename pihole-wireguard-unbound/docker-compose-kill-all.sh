#!/usr/bin/env bash

ENV_FILE="./.env"
PIHOLE_NETWORK_NAME="pihole_vpn"

source "${ENV_FILE}" || return 1

docker-compose kill
docker container rm ${PIHOLE_CONTAINER_NAME} ${WIREGUARD_CONTAINER_NAME} "${UNBOUND_CONTAINER_NAME}"
docker network rm "${PIHOLE_NETWORK_NAME}"
docker image rm "${WIREGUARD_IMAGE_NAME}"
docker image rm "${PIHOLE_IMAGE_NAME}"
docker image rm "${UNBOUND_IMAGE_NAME}"
