#! /bin/sh
set -e

docker="$(which docker 2>/dev/null || true)"
[ -z "$docker" ] && docker="$(which podman 2>/dev/null || true)"
[ -z "$docker" ] && {
	echo "No compatible Docker analogue found"
	exit 1
}
composefile="contrib/docker-compose-dev.yml"
[ -r "$composefile" ] || {
	echo "Could not read compose file: $composefile"
	exit 2
}

"$docker" compose -f "$composefile" up --build --force-recreate
