#!/usr/bin/env bash

MEDIA_DIR="/media/torrent-downloads/finished"
CONFIG_DIR="/opt/jellyfin/config-dir"
CACHE_DIR="/opt/jellyfin/cache-dir"
JELLYFIN_CONTAINER_NAME="jellyfin"
JELLYFIN_IMAGE="jellyfin/jellyfin"
JELLYFIN_VERSION="latest"

set -e

clear

printf "\n\n[\x1B[0;1;38;5;46mDONE\x1B[0m]\n\n"

docker run                                            \
  --detach                                            \
  --name "${JELLYFIN_CONTAINER_NAME}"                 \
  --net=host                                          \
  --volume ${CONFIG_DIR}:/config                      \
  --volume ${CACHE_DIR}:/cache                        \
  --mount type=bind,source=${MEDIA_DIR},target=/media \
  --restart=unless-stopped                            \
  ${JELLYFIN_IMAGE}:${JELLYFIN_VERSION}

printf "\n\n[\x1B[0;1;38;5;46mDONE\x1B[0m]\n\n"

## Possible Options
# docker run -d \
#  --name=jellyfin \
#  --volume /path/to/config:/config \
#  --volume /path/to/cache:/cache \
#  --volume /path/to/media:/media \
#  --user 1000:1000 \
#  --net=host \
#  --restart=unless-stopped \
#  --runtime=nvidia \ # https://jellyfin.org/docs/general/administration/hardware-acceleration/nvidia
#  --gpus all \
#  jellyfin/jellyfin

