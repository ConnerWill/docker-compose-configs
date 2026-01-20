#!/usr/bin/env bash
# update-jellyfin-stack.sh
# Purpose: Safely pull latest images and recreate containers only when needed
# Best practices: strict mode, logging, printf everywhere, optional service filter

set -euo pipefail          # Exit on error, undefined vars, pipeline failures
IFS=$'\n\t'                # Safer word splitting

# ──────────────────────────────────────────────────────────────────────────────
#  Configuration
# ──────────────────────────────────────────────────────────────────────────────

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
LOG_FILE="${LOG_FILE:-/var/log/docker-update.log}"
MAX_LOG_SIZE=1048576       # 1 MiB — rotate when bigger

# Colors (only if terminal supports)
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    NC='\033[0m'        # No Color
else
    RED='' GREEN='' YELLOW='' NC=''
fi

# ──────────────────────────────────────────────────────────────────────────────
#  Helper functions
# ──────────────────────────────────────────────────────────────────────────────

log() {
    local level="$1"
    shift
    printf "[%s] %-8s %s\n" "$(date '+%Y-%m-%d %H:%M:%S')" "$level" "$*" \
        | tee -a "$LOG_FILE"
}

info()  { log "INFO"  "$@"; }
warn()  { log "WARN"  "${YELLOW}$*${NC}"; }
error() { log "ERROR" "${RED}$*${NC}" >&2; }

rotate_log() {
    [[ ! -f "$LOG_FILE" ]] && return
    local size
    size=$(stat -c %s "$LOG_FILE" 2>/dev/null || stat -f %z "$LOG_FILE" 2>/dev/null || echo 0)
    (( size <= MAX_LOG_SIZE )) && return

    mv "$LOG_FILE" "${LOG_FILE}.1"
    info "Log rotated (size exceeded ${MAX_LOG_SIZE} bytes)"
}

check_prerequisites() {
    if ! command -v docker compose >/dev/null 2>&1; then
        error "docker compose not found. This script requires Docker Compose v2."
        exit 1
    fi

    if [[ ! -f "$COMPOSE_FILE" ]]; then
        error "Compose file not found: %s" "$COMPOSE_FILE"
        exit 1
    fi
}

# ──────────────────────────────────────────────────────────────────────────────
#  Main logic
# ──────────────────────────────────────────────────────────────────────────────

main() {
    rotate_log
    info "Starting update for compose project in %s" "$(pwd)"

    check_prerequisites

    local service_filter=""
    if [[ $# -gt 0 ]]; then
        service_filter="$*"
        info "Updating only service(s): %s" "$service_filter"
    else
        info "Updating all services"
    fi

    info "Pulling latest images..."
    if ! docker compose -f "$COMPOSE_FILE" pull $service_filter; then
        warn "Pull failed — continuing anyway (might be network issue)"
    fi

    info "Recreating containers (only changed ones will be replaced)..."
    docker compose -f "$COMPOSE_FILE" up -d --remove-orphans $service_filter

    info "Cleaning up old/unused images..."
    docker image prune -f >/dev/null 2>&1 || true

    # Quick status
    printf "\n"
    docker compose -f "$COMPOSE_FILE" ps --format "table {{.Name}}\t{{.State}}\t{{.Status}}"

    info "Update completed successfully ✓"
    printf "${GREEN}Done.${NC}\n"
}

# ──────────────────────────────────────────────────────────────────────────────
#  Entry point
# ──────────────────────────────────────────────────────────────────────────────

trap 'error "Script interrupted — state may be inconsistent"' INT TERM
trap 'error "Unexpected error occurred"' ERR

main "$@"
exit 0

