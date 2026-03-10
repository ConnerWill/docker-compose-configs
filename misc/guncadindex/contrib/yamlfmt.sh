#! /bin/sh
set -e

docker="$(which docker 2>/dev/null || true)"
[ -z "$docker" ] && docker="$(which podman 2>/dev/null || true)"
[ -z "$docker" ] && {
	echo "No compatible Docker analogue found"
	exit 1
}

"$docker" run --rm -v "$PWD:/project" -it ghcr.io/google/yamlfmt:latest "$@"
