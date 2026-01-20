#!/usr/bin/env bash

## OPTIONS

set -e

## VARIABLES

SCRIPT_PATH="$(realpath "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(dirname "${SCRIPT_PATH}")"
DOCKER_COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"
ENV_FILE="${SCRIPT_DIR}/.env"
TEXT_GREEN='\x1B[38;5;46m'
TEXT_RED='\x1B[38;5;196m'
TEXT_RESET='\x1B[0m'

## FUNCTIONS

function die(){
  local input_msg
  input_msg="${1}"
  printf "${TEXT_RED}ERROR: %s${TEXT_RESET}\n" "${input_msg}"
  exit 1
}

function success(){
  local input_msg
  input_msg="${1}"
  printf "${TEXT_GREEN}SUCCESS: %s${TEXT_RESET}\n" "${input_msg}"
}

function file_exists(){
  local input_file
  input_file="${1}"
  if [[ ! -e "${input_file}" ]]; then
    die "Cannot find file: '${input_file}'"
  fi
}

function source_file(){
  local input_file
  input_file="${1}"
  if [[ -e "${input_file}" ]]; then
    if source "${input_file}"; then
      die "Unable to source file: '${input_file}'"
    fi
  fi
}

function is_installed(){
  local input_pkg
  input_pkg="${1}"
  if ! command -v "${input_pkg}" >/dev/null 2>&1; then
    die "Could not find '${input_pkg}' in PATH"
  fi
}

function start_docker(){
  if docker-compose --file "${DOCKER_COMPOSE_FILE}" --env-file "${ENV_FILE}" up --wait --detach; then
    success "Started docker-compose: ${JELLYFIN_NAME}"
  else
    die "Failed to start docker-compose"
  fi
}

## MAIN

file_exists "${DOCKER_COMPOSE_FILE}"
file_exists "${ENV_FILE}"
source_file "${ENV_FILE}"
is_installed "docker"
is_installed "docker-compose"
start_docker
