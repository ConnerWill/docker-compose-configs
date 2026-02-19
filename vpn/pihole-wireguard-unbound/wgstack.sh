#!/usr/bin/env bash
#
# wgstack - wrapper around Docker Compose for WireGuard + Pi-hole + Unbound
#
# Behavior:
# - Requires an env file (default: ./.env). Fails if missing.
# - Always passes --env-file <file> to Compose so env vars are used for interpolation,
#   including container_name fields that reference ${...}.
# - Prefers Docker Compose v2 plugin (docker compose), else docker-compose.

set -euo pipefail
IFS=$'\n\t'

###############################################################################
# Globals
###############################################################################
readonly SCRIPT_PATH="${0}"
readonly SCRIPT_NAME="${SCRIPT_PATH##*/}"
readonly SCRIPT_DIR="$(
  # Avoid cd/pwd resolution. Just compute the containing path segment.
  if [[ "${SCRIPT_PATH}" == */* ]]; then
    printf "%s\n" "${SCRIPT_PATH%/*}"
  else
    printf "%s\n" "."
  fi
)"
readonly DESCRIPTION="Wrapper for Docker Compose stack (wireguard + pihole + unbound)"
readonly DEFAULT_ENV_FILE=".env"

die() {
  local msg="${1}"
  printf "ERROR: %s\n" "${msg}" >&2
  exit 1
}

set_compose_bin() {
  # Set the global array COMPOSE_BIN to either:
  #   ("docker" "compose")  # v2 plugin
  # or
  #   ("docker-compose")    # v1
  #
  # This avoids string splitting (which breaks if IFS doesn't include spaces).
  if command -v docker >/dev/null 2>&1; then
    if docker compose version >/dev/null 2>&1; then
      COMPOSE_BIN=("docker" "compose")
      return 0
    fi
  fi

  if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_BIN=("docker-compose")
    return 0
  fi

  die "Neither 'docker compose' nor 'docker-compose' found."
}

show_help() {
  cat <<EOF
${SCRIPT_NAME} - ${DESCRIPTION}

USAGE:
  ${SCRIPT_NAME} [global-compose-flags...] [wrapper-options...] [command] [command-args...] [services...]

ENV FILE (REQUIRED):
  By default, this script requires: ./${DEFAULT_ENV_FILE}
  You may override with: --env-file <path>
  The env file is always passed to Compose so variables are used for interpolation
  (e.g. container_name: \${WIREGUARD_CONTAINER_NAME}).

DEFAULT BEHAVIOR:
  ${SCRIPT_NAME}
    -> up --pull always --yes --detach wireguard pihole unbound

COMMANDS:
  up          Start (default)
  down        Stop and remove containers/networks (volumes not removed unless you pass -v)
  restart     Restart services
  pull        Pull images
  logs        Tail logs (follows by default)
  ps          Show status
  config      Render final compose config

WRAPPER OPTIONS:
  -d, --dry-run            Use Compose dry-run mode (no changes applied)
  -f, --force-recreate     Force recreation (only applies to 'up')
  --all                    Apply command to all services in compose file (no default service list)
  --only SERVICE           Limit to a single service (repeatable)
  --no-default-services    Don't append default services unless you specify them explicitly
  --no-detach              For 'up': run attached (foreground)
  --print                  Print the composed command (shell-escaped), don't execute
  -h, --help               Show help

GLOBAL COMPOSE FLAGS (PASSTHROUGH, placed before command):
  -p, --project-name NAME
  --file FILE              (compose file; wrapper uses -f for force-recreate)
  --env-file FILE
  --profile NAME
  --project-directory DIR

EXAMPLES:
  ${SCRIPT_NAME}
  ${SCRIPT_NAME} up
  ${SCRIPT_NAME} --env-file .env.prod up
  ${SCRIPT_NAME} --dry-run up
  ${SCRIPT_NAME} up --force-recreate
  ${SCRIPT_NAME} up --only wireguard
  ${SCRIPT_NAME} logs --only pihole
  ${SCRIPT_NAME} --all down
  ${SCRIPT_NAME} --print up --force-recreate
EOF
}

print_cmd() {
  local -a argv=("${@}")
  local i

  for i in "${!argv[@]}"; do
    printf "%q" "${argv[${i}]}"
    if (( ${i} < ${#argv[@]} - 1 )); then
      printf " "
    fi
  done
  printf "\n"
}

main() {
  # Set by set_compose_bin()
  local -a COMPOSE_BIN=()
  set_compose_bin

  local -a global_args=()
  local -a cmd_args=()
  local -a services=()
  local -a passthrough=()

  local cmd="up"
  local dry_run=false
  local force_recreate=false
  local print_only=false
  local use_default_services=true
  local all_services=false
  local detach=true

  local -a default_services=("wireguard" "pihole" "unbound")

  # Env file handling:
  local env_file_path="./${DEFAULT_ENV_FILE}"
  local user_set_env_file=false

  # Parse args
  while (( $# > 0 )); do
    case "${1}" in
      -h|--help|help|-help)
        show_help
        return 0
        ;;

      -d|--dry-run|--dryrun|--dry)
        dry_run=true
        shift
        ;;
      -f|--force|--recreate|--force-recreate)
        force_recreate=true
        shift
        ;;
      --print)
        print_only=true
        shift
        ;;
      --all)
        all_services=true
        shift
        ;;
      --no-default-services)
        use_default_services=false
        shift
        ;;
      --no-detach)
        detach=false
        shift
        ;;
      --only)
        shift
        (( $# > 0 )) || die "--only requires a service name"
        services+=("${1}")
        use_default_services=false
        shift
        ;;

      # Compose global flags (must appear before the command)
      -p|--project-name|--profile|--project-directory|--file)
        local flag="${1}"
        shift
        (( $# > 0 )) || die "${flag} requires a value"
        global_args+=("${flag}" "${1}")
        shift
        ;;
      --env-file)
        shift
        (( $# > 0 )) || die "--env-file requires a value"
        env_file_path="${1}"
        user_set_env_file=true
        shift
        ;;

      # Command selection
      up|down|restart|pull|logs|ps|config)
        cmd="${1}"
        shift
        ;;

      --)
        shift
        while (( $# > 0 )); do
          passthrough+=("${1}")
          shift
        done
        ;;

      *)
        passthrough+=("${1}")
        shift
        ;;
    esac
  done

  # Require env file
  if [[ ! -f "${env_file_path}" ]]; then
    if [[ "${user_set_env_file}" == "true" ]]; then
      die "Env file not found: ${env_file_path}"
    fi
    die "Missing required env file in current directory: ${env_file_path}"
  fi

  # Always pass env file to Compose so interpolation uses it
  global_args+=(--env-file "${env_file_path}")

  if [[ "${dry_run}" == "true" ]]; then
    global_args+=(--dry-run)
  fi

  # Build command args
  case "${cmd}" in
    up)
      cmd_args=(up --pull always)
      if [[ "${detach}" == "true" ]]; then
        cmd_args+=(--detach)
      fi
      cmd_args+=(--yes)
      if [[ "${force_recreate}" == "true" ]]; then
        cmd_args+=(--force-recreate)
      fi
      ;;
    down)
      cmd_args=(down)
      ;;
    restart)
      cmd_args=(restart)
      ;;
    pull)
      cmd_args=(pull)
      ;;
    logs)
      cmd_args=(logs --follow --tail=200)
      ;;
    ps)
      cmd_args=(ps)
      ;;
    config)
      cmd_args=(config)
      ;;
    *)
      die "Unsupported command: ${cmd}"
      ;;
  esac

  # Decide which services to append
  if [[ "${all_services}" == "true" ]]; then
    :
  elif (( ${#services[@]} > 0 )); then
    :
  elif [[ "${use_default_services}" == "true" ]]; then
    services=("${default_services[@]}")
  fi

  local -a argv=()
  argv+=("${COMPOSE_BIN[@]}")
  argv+=("${global_args[@]}")
  argv+=("${cmd_args[@]}")
  argv+=("${passthrough[@]}")

  case "${cmd}" in
    up|restart|pull|logs|ps)
      if (( ${#services[@]} > 0 )); then
        argv+=("${services[@]}")
      fi
      ;;
    *)
      :
      ;;
  esac

  if [[ "${print_only}" == "true" ]]; then
    print_cmd "${argv[@]}"
    return 0
  fi

  "${argv[@]}"
}

main "${@}"
