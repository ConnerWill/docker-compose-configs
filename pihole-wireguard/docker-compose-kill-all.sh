#!/usr/bin/env bash

docker-compose kill
docker container rm pihole-pihole pihole-wireguard
docker network rm pihole_vpn
docker image rm lscr.io/linuxserver/wireguard:latest
docker image rm pihole/pihole:latest
