#!/usr/bin/env bash

ENV_FILE="./.env"
ROOT_HINTS_URL="https://www.internic.net/domain/named.cache"

source "${ENV_FILE}" || return 1

curl -o "${UNBOUND_CONFIG_DIR}/root.hints" "${ROOT_HINTS_URL}"
