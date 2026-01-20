#!/usr/bin/env bash


# https://jellyfin.org/docs/general/post-install/transcoding/hardware-acceleration/nvidia

## OPTIONS

set -euo pipefail
IFS=$'\n\t'

## VARIABLES

SCRIPT_PATH="$(realpath "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(dirname "${SCRIPT_PATH}")"
DOCKER_COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"
ENV_FILE="${SCRIPT_DIR}/.env"
TEXT_GREEN='\x1B[38;5;46m'
TEXT_YELLOW='\x1B[38;5;226m'
TEXT_RED='\x1B[38;5;196m'
TEXT_RESET='\x1B[0m'
SLEEP_TIME=5

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

function information(){
  local input_msg
  input_msg="${1}"
  printf "${TEXT_YELLOW}INFO: %s${TEXT_RESET}\n" "${input_msg}"
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
    if ! source "${input_file}"; then
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

is_installed "docker"
source_file "${ENV_FILE}"
source_file "/etc/os-release"

if [[ "${ID}" != "arch" ]]; then
  die "This setup script only works on Arch Linux"
fi

# Update system
information "Updating system ..."
sudo pacman -Syu --needed --noconfirm

# Install the Archlinux/extra jellyfin-ffmpeg package
# Install the NVIDIA proprietary driver. Then install an extra package for NVENC and NVDEC support
information "Installing packages ..."
sudo pacman -S --needed --noconfirm jellyfin-ffmpeg nvidia-open nvidia-utils nvidia-settings nvidia-container-toolkit

# Restart docker
information "Restarting docker ..."
sudo systemctl restart docker

# Test GPU in host
information "Testing GPU in host ..."
if nvidia-smi; then
    success "Host GPU detected"
    information "Sleeing for ${SLEEP_TIME} seconds ..."
    sleep "${SLEEP_TIME}"
else
    die "Host GPU NOT detected"
fi

# Test GPU in container
information "Testing GPU in container ..."
if docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi; then
    success "GPU detected inside Docker"
    information "Sleeing for ${SLEEP_TIME} seconds ..."
    sleep "${SLEEP_TIME}"
else
    die "GPU NOT detected inside Docker"
fi

# Add your username to the video group
information "Adding user: '${USER}' to 'video' group ..."
sudo usermod -aG video "${USER}"
information "You need to log out and log back in for this group change to take effect ..."
information "Sleeing for ${SLEEP_TIME} seconds ..."
sleep "${SLEEP_TIME}"


information "Starting of work inside running '${JELLYFIN_NAME}' container"
information "if container: '${JELLYFIN_NAME}' is not running, this will fail... sleeping for ${SLEEP_TIME} seconds ..."
sleep "${SLEEP_TIME}"

# Update dynamic links and restart the Docker service
information "Updating dynamic links in running '${JELLYFIN_NAME}' container"
docker exec -it "${JELLYFIN_NAME}" ldconfig
information "Sleeing for ${SLEEP_TIME} seconds ..."
sleep "${SLEEP_TIME}"

# Restart docker
information "Restarting docker ..."
sudo systemctl restart docker

# Check the NVIDIA GPU's status by using nvidia-smi
information "Testing NVIDIA GPU status in running '${JELLYFIN_NAME}' container ..."
docker exec -it "${JELLYFIN_NAME}" nvidia-smi
information "Sleeing for ${SLEEP_TIME} seconds ..."
sleep "${SLEEP_TIME}"
