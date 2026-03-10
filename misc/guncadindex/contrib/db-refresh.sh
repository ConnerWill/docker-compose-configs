#!/bin/bash
set -e

sqlfile="./dmp.sql.gz"
dbcontainer="guncad-index_db_1"
if ! [ -e "$sqlfile" ]; then
	echo "Database dump does not exist: $sqlfile"
fi

docker="$(which docker 2>/dev/null || true)"
[ -z "$docker" ] && docker="$(which podman 2>/dev/null || true)"
[ -z "$docker" ] && {
	echo "No compatible Docker analogue found"
	exit 1
}

echo "Importing database dump. Please ensure database is up as $dbcontainer"
"$docker" exec -i "$dbcontainer" psql -U django django -c "DROP SCHEMA PUBLIC CASCADE; CREATE SCHEMA PUBLIC;"
zcat "$sqlfile" | "$docker" exec -i "$dbcontainer" psql -U django django
