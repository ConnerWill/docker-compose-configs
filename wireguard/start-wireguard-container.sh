#!/bin/bash
set -Eeuo pipefail
#trap 'printf "${COLOR_RED}ERROR${COLOR_RESET} occurred at line %d. Exiting.\n" "${LINENO}" >&2' ERR

# Configuration variables for WireGuard and Docker Compose
WIREGUARD_DIR="${HOME}/vpn/wireguard"
DOCKER_COMPOSE_FILE_DIR="${WIREGUARD_DIR}"
DOCKER_COMPOSE_FILE="${DOCKER_COMPOSE_FILE_DIR}/docker-compose.yml"
WIREGUARD_CONFIG_DIR="${WIREGUARD_DIR}/config"
WIREGUARD_CONTAINER_NAME="wireguard"
SLEEP_TIME=2  # Pause duration in seconds after start/stop operations
SCRIPT_DESCRIPTION="Helper script to manage docker-compose"
SCRIPT_NAME="$(basename "${0}")"
COLOR_RED='\x1B[0;38;5;196m'
COLOR_GREEN='\x1B[0;38;5;46m'
COLOR_YELLOW='\x1B[0;38;5;226m'
COLOR_MAGENTA='\x1B[0;38;5;201m'
COLOR_BLUE='\x1B[0;38;5;21m'
COLOR_RESET='\x1B[0m'
COLOR_LINE="${COLOR_MAGENTA}"

draw_line() {
    local char="${1:--}"  # Default to "-" if no character provided
    local width
    width=$(tput cols 2>/dev/null || echo 80)
    printf "${COLOR_LINE}%*s${COLOR_RESET}\n" "$width" '' | tr ' ' "$char"
}

# Display WireGuard configuration with validation
show_wireguard_config() {
    # Validate directories and file
    local errors=0
    if [[ ! -d "${WIREGUARD_DIR}" ]]; then
        printf "${COLOR_RED}Warning${COLOR_RESET}: WireGuard directory '%s' does not exist.\n" "${WIREGUARD_DIR}"
        errors=$((errors + 1))
    fi
    if [[ ! -d "${WIREGUARD_CONFIG_DIR}" ]]; then
        printf "${COLOR_RED}Warning${COLOR_RESET}: WireGuard config directory '%s' does not exist.\n" "${WIREGUARD_CONFIG_DIR}"
        errors=$((errors + 1))
    fi
    if [[ ! -f "${DOCKER_COMPOSE_FILE}" ]]; then
        printf "${COLOR_RED}Warning${COLOR_RESET}: Docker Compose file '%s' does not exist.\n" "${DOCKER_COMPOSE_FILE}"
        errors=$((errors + 1))
    fi

    draw_line "-"

    # Display configuration
    printf "WireGuard Configuration:\n"
    printf "==========================\n"
    printf "WireGuard Directory:        %s\n" "${WIREGUARD_DIR}"
    printf "WireGuard Config Directory: %s\n" "${WIREGUARD_CONFIG_DIR}"
    printf "Compose File Directory:     %s\n" "${DOCKER_COMPOSE_FILE_DIR}"
    printf "Compose File:               %s\n" "${DOCKER_COMPOSE_FILE}"
    printf "Container Name:             %s\n" "${WIREGUARD_CONTAINER_NAME}"
    printf "Sleep Time:                 %s seconds\n" "${SLEEP_TIME}"
    
    draw_line "-"

    [[ ${errors} -eq 0 ]] && return 0 || return 1

    sleep "${SLEEP_TIME}"
}

# Check if a file exists
check_file_exists() {
    local file="${1}"
    if [[ -z "${file}" ]]; then
        printf "${COLOR_RED}ERROR${COLOR_RESET}: No file path provided.\n" >&2
        return 1
    fi
    if [[ -e "${file}" ]]; then
        printf "${COLOR_GREEN}File '%s' exists.${COLOR_RESET}\n" "${file}"
        return 0
    else
        printf "${COLOR_RED}File '%s' does not exist.${COLOR_RESET}\n" "${file}" >&2
        return 1
    fi
}

# Safely change to a directory
safe_cd() {
    local dir="${1}"
    if [[ -z "${dir}" ]]; then
        printf "${COLOR_RED}ERROR${COLOR_RESET}: No directory provided.\n" >&2
        return 1
    fi
    if [[ ! -d "${dir}" ]]; then
        printf "${COLOR_RED}ERROR${COLOR_RESET}: Directory '%s' does not exist.\n" "${dir}" >&2
        return 1
    fi
    if [[ ! -r "${dir}" ]] || [[ ! -x "${dir}" ]]; then
        printf "${COLOR_RED}ERROR${COLOR_RESET}: Directory '%s' is not accessible.\n" "${dir}" >&2
        return 1
    fi
    if cd "${dir}" 2>/dev/null; then
        printf "${COLOR_GREEN}Successfully changed to directory '%s'.${COLOR_RESET}\n" "${dir}"
        return 0
    else
        printf "${COLOR_RED}ERROR${COLOR_RESET}: Failed to change to directory '%s'.\n" "${dir}" >&2
        return 1
    fi
}

# Validate Docker Compose file content
check_docker_compose() {
    local compose_file="${1:-${DOCKER_COMPOSE_FILE}}"
    if ! check_file_exists "${compose_file}"; then
        return 1
    fi
    if ! command -v docker-compose >/dev/null 2>&1; then
        printf "${COLOR_RED}ERROR${COLOR_RESET}: docker-compose is not installed.\n" >&2
        return 1
    fi
    if docker-compose -f "${compose_file}" config >/dev/null 2>&1; then
        printf "${COLOR_GREEN}Docker Compose file '%s' is valid.${COLOR_RESET}\n" "${compose_file}"
        return 0
    else
        printf "${COLOR_RED}ERROR${COLOR_RESET}: Docker Compose file '%s' is invalid.\n" "${compose_file}" >&2
        return 1
    fi
}

# Validate SLEEP_TIME
validate_sleep_time() {
    if ! [[ "${SLEEP_TIME}" =~ ^[0-9]+$ ]] || [[ "${SLEEP_TIME}" -le 0 ]]; then
        printf "${COLOR_RED}ERROR${COLOR_RESET}: SLEEP_TIME '%s' must be a positive integer.\n" "${SLEEP_TIME}" >&2
        return 1
    fi
    return 0
}

# Start the WireGuard Docker container
start_wireguard() {
    if ! check_docker_compose "${DOCKER_COMPOSE_FILE}"; then
        return 1
    fi
    if ! safe_cd "${DOCKER_COMPOSE_FILE_DIR}"; then
        return 1
    fi
    if ! validate_sleep_time; then
        return 1
    fi
    if docker-compose -f "${DOCKER_COMPOSE_FILE}" up -d 2>/dev/null; then
        printf "${COLOR_GREEN}WireGuard container '%s' started successfully.${COLOR_RESET}\n" "${WIREGUARD_CONTAINER_NAME}"
        printf "Pausing for %s seconds...\n" "${SLEEP_TIME}"
        sleep "${SLEEP_TIME}"
        return 0
    else
        printf "${COLOR_RED}ERROR${COLOR_RESET}: Failed to start WireGuard container '%s'.\n" "${WIREGUARD_CONTAINER_NAME}" >&2
        return 1
    fi
}

# Stop the WireGuard Docker container
stop_wireguard() {
    if ! check_docker_compose "${DOCKER_COMPOSE_FILE}"; then
        return 1
    fi
    if ! safe_cd "${DOCKER_COMPOSE_FILE_DIR}"; then
        return 1
    fi
    if ! validate_sleep_time; then
        return 1
    fi
    if docker-compose -f "${DOCKER_COMPOSE_FILE}" down 2>/dev/null; then
        printf "${COLOR_GREEN}WireGuard container '%s' stopped successfully.${COLOR_RESET}\n" "${WIREGUARD_CONTAINER_NAME}"
        printf "Pausing for %s seconds...\n" "${SLEEP_TIME}"
        sleep "${SLEEP_TIME}"
        return 0
    else
        printf "${COLOR_RED}ERROR${COLOR_RESET}: Failed to stop WireGuard container '%s'.\n" "${WIREGUARD_CONTAINER_NAME}" >&2
        return 1
    fi
}

# Check the status of the WireGuard Docker container
check_wireguard_status() {
    if ! command -v docker >/dev/null 2>&1; then
        printf "${COLOR_RED}ERROR${COLOR_RESET}: docker is not installed.\n" >&2
        return 1
    fi
    if docker ps -q -f name="${WIREGUARD_CONTAINER_NAME}" | grep -q .; then
        printf "${COLOR_GREEN}WireGuard container '%s' is running.${COLOR_RESET}\n" "${WIREGUARD_CONTAINER_NAME}"
        return 0
    else
        printf "${COLOR_YELLOW}WireGuard container '%s' is not running.${COLOR_RESET}\n" "${WIREGUARD_CONTAINER_NAME}"
        return 1
    fi
}

# Check the logs of the container
check_docker_compose_logs() {
    draw_line "-"

    if ! command -v docker >/dev/null 2>&1; then
        printf "${COLOR_RED}ERROR${COLOR_RESET}: docker is not installed.\n" >&2
        return 1
    fi
    if docker logs "${WIREGUARD_CONTAINER_NAME}"; then
        draw_line "-"
        return 0
    else
        printf "${COLOR_YELLOW}ERROR${COLOR_RESET}: Unable to show logs for '%s'.${COLOR_RESET}\n" "${WIREGUARD_CONTAINER_NAME}"
        return 1
    fi

}

# Display usage information
usage() {

draw_line "="

    cat <<EOH
NAME:
  ${SCRIPT_NAME}

DESCRIPTION:
  ${SCRIPT_DESCRIPTION}

USAGE:
  ${SCRIPT_NAME} {config|start|stop|status|check|logs|help}

OPTIONS:
  config  - Show WireGuard configuration
  start   - Start the WireGuard container
  stop    - Stop the WireGuard container
  status  - Check the status of the WireGuard container
  check   - Validate the Docker Compose file
  logs    - Show Docker container logs
  help    - Show help menu
EOH

draw_line "="

}

# Main execution with command-line argument parsing
main() {
    local command="${1}"
    case "${command}" in
        config)
            show_wireguard_config
            ;;
        start)
            start_wireguard
            ;;
        stop)
            stop_wireguard
            ;;
        status)
            check_wireguard_status
            ;;
        check)
            check_docker_compose
            ;;
        logs)
            check_docker_compose_logs
            ;;
        ""|help|-h|--help)
            usage
            ;;
        *)
            printf "${COLOR_RED}ERROR${COLOR_RESET}: Unknown command '%s'.\n" "${command}" >&2
            usage
            return 1
            ;;
    esac
}

main "${@}"
