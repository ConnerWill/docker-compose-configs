#!/usr/bin/env bash

set -e

declare -a compose_args
compose_args=(
  up
  --force-recreate
  --pull always
  --yes
  --detach
)

is_installed(){
  local pkg found_pkg
  pkg="${1}"
  if command -v "${pkg}" >/dev/null 2>&1; then
    found_pkg="$(command -v ${pkg} || true)"
    echo "${found_pkg}"
  else
    printf "Cannot find '%s' in PATH\n" >2
    return 1
  fi
}

# TODO: Fix this. make better arg passing
if [[ "${1}" == "-d" || "${1}" == "--dry-drun" || "${1}" == "--dryrun" || "${1}" == "--dry" ]]; then
  compose_args+=( --dry-run )
fi

compose_bin="$(is_installed 'docker-compose')"
"${compose_bin}" "${compose_args[@]}"
