#! /bin/bash
# GunCAD Index Docker entrypoint
set -e

# What user should we drop privs to if we're root?
targetuser="django"

#
# We set this envvar in the Dockerfile
# Please DO NOT override this so you can run it in your shell
#
if [ -z "$GUNCAD_IN_DOCKER" ]; then
	echo "Don't run this in your shell -- see the test scripts in contrib"
	echo "This is an entrypoint for the Docker container"
	exit 1
fi

# If we get this far, we should be in Docker

# If we're root, take advantage before dropping privs
# When we drop privs we'll just reexec the script as the target user, specified above
if [ "$(id -u)" -eq "0" ]; then
	case "$1" in
		gunicorn|cron)
			echo "Running as root -- doing some preambulatory configuration"
			echo "  Changing ownership of /data..."
			chown -R "$targetuser": /data /home/"$targetuser"
			ls -alh /data
			;;
		lbrynet)
			echo "Running as root -- doing some preambulatory configuration"
			echo "  Changing ownership of LBRY dirs..."
			chown -R "$targetuser": /home/"$targetuser"
			;;
		*)
			echo "Running as root -- dropping privs"
			;;
	esac
	echo "Pivoting to $targetuser"
	echo "Current args: $@"
	exec su "$targetuser" -s /bin/bash -c "$(realpath "$0") $@"
fi

# If we're here, we're an unprivileged user and should start the app up
echo "Running as user: $(whoami) (UID $(id -u))"
if [ -n "$GUNCAD_COMMIT_TAG" ]; then
	export GUNCAD_COMMIT_REF="$GUNCAD_COMMIT_TAG"
elif [ -n "$GUNCAD_COMMIT_SHA" ]; then
	export GUNCAD_COMMIT_REF="$GUNCAD_COMMIT_SHA"
else
	export GUNCAD_COMMIT_REF="master"
fi
# Source in local envvars if we have them
if [ -e "./.local.env" ]; then
	echo "Sourcing in ./.local.env"
	. ./.local.env
fi
echo "Git ref of build:"
echo "  GUNCAD_COMMIT_REF:             ${GUNCAD_COMMIT_REF:-Unset}"
if [ -n "$GUNCAD_DEBUG" ] && [ -z "$GUNCAD_SITE_WARNING_BANNER" ]; then
	echo "Debug mode is enabled -- setting default warning banner"
	ls -alh /app
	export GUNCAD_SITE_WARNING_BANNER="DEBUG"
fi
echo "LLM Configuration:"
if [ -n "$GUNCAD_AI_XAI_API_KEY" ]; then
	echo "  GUNCAD_AI_XAI_API_KEY          Set"
else
	echo "  GUNCAD_AI_*                    Unset"
fi
echo "Configuration variables:"
echo "  GUNCAD_DEBUG:                  ${GUNCAD_DEBUG:-Unset}"
echo "  GUNCAD_DB_USER:                ${GUNCAD_DB_USER}"
echo "  GUNCAD_DB_NAME:                ${GUNCAD_DB_NAME}"
echo "  GUNCAD_DB_HOST:                ${GUNCAD_DB_HOST}"
echo "  GUNCAD_DB_PORT:                ${GUNCAD_DB_PORT}"
echo "  GUNCAD_STATSD_HOST:            ${GUNCAD_STATSD_HOST:-Unset}"
echo "  GUNCAD_STATSD_PORT:            ${GUNCAD_STATSD_PORT:-Unset}"
echo "  GUNCAD_SITE_NAME:              ${GUNCAD_SITE_NAME:-Unset}"
echo "  GUNCAD_SITE_TAGLINE:           ${GUNCAD_SITE_TAGLINE:-Unset (you will be bugged for this)}"
echo "  GUNCAD_ALLOWED_HOSTS:          ${GUNCAD_ALLOWED_HOSTS:-Unset}"
echo "  GUNCAD_TRACK_UPDATES:          ${GUNCAD_TRACK_UPDATES:-Unset}"
echo "  GUNCAD_TRACK_ODYSEE:           ${GUNCAD_TRACK_ODYSEE:-Unset}"
if [ -z "$GUNCAD_SECRET_KEY" ]; then
	echo "  GUNCAD_SECRET_KEY:             DEFAULT! CHANGE THIS!"
else
	echo "  GUNCAD_SECRET_KEY:             Set"
fi

# Set up some envvars that the user doesn't need control over
tmpdir_prometheus="$(mktemp -d)"
export PROMETHEUS_MULTIPROC_DIR="$tmpdir_prometheus"

# Now, figure out what we need to be running
case "$1" in
	cron)
		echo "Becoming cron daemon..."
		set +e
		# If we were told "cron", we should begin spinning up a background service
		# that just runs a bunch of tasks on repeat.
		python3 manage.py import-tagfile default-tags.yml		# Import tags, case we have new ones
		nice -n 10 python3 manage.py wait-for-wallet
		nice -n 10 python3 manage.py import-channels seed_channels.csv  # Start new instances and self-hosteds off right
		nice -n 10 python3 manage.py tag				# Tag releases. This cleans up after interrupted runs
		while true; do
			# Arm a minimum delay timer, fire the jobs, then wait
			sleep "${GUNCAD_CRON_MINIMUM_DELAY:-3600}" &
			echo "$(date -Iseconds) - cronjob firing"
			nice -n 10 bash cron.sh
			echo "$(date -Iseconds) - sleeping until timer"
			# This here should wait for the timer to finish up. If cron.sh takes longer
			# than the sleep timeout, wait will return immediately
			wait
		done
		exit 1
		;;
	lbrynet)
		echo "Becoming lbrynet daemon..."
		# If we were told to become the lbrynet daemon, just do that directly
		# First, unset some stuff for security
		unset ${!GUNCAD_DB*} ${!GUNCAD_SECRET*}
		# https://github.com/lbryio/lbry-sdk
		# Note that "start" MUST come before the other args
		exec lbrynet start \
			--api 0.0.0.0:5279
		;;
	gunicorn)
		echo "Becoming gunicorn webserver..."
		# If we're in DEBUG, run collectstatic on app boot
		if [ -n "$GUNCAD_DEBUG" ]; then
			echo "Collecting static assets..."
			python3 manage.py collectstatic \
				--noinput
		elif [ -w "/data/static" ]; then
			echo "Copying static assets to /data/static..."
			cp -r /static/* /data/static
			find /data/static -type f -exec chmod 0644 {} +
			find /data/static -type d -exec chmod 0755 {} +
		fi
		# Migrate
		python3 manage.py migrate
		# That's really the only thing that should block startup. Now, we configure Gunicorn
		extraargs=""
		if [ -n "$GUNCAD_DEBUG" ]; then
			extraargs="$extraargs --reload"
		else
			extraargs="$extraargs --preload"
		fi
		if [ -n "$GUNCAD_STATSD_HOST" ] && [ -n "$GUNCAD_STATSD_PORT" ]; then
			echo "Enabling statsd configuration: --statsd-host=$GUNCAD_STATSD_HOST:$GUNCAD_STATSD_PORT"
			extraargs="$extraargs --statsd-host=$GUNCAD_STATSD_HOST:$GUNCAD_STATSD_PORT --statsd-prefix=guncadindex"
		fi
		#
		# Lastly, we're going to spin off a Prometheus stats collector thread
		# One might rightfully ask:
		#
		# >Why is this not pull-oriented like Prometheus is supposed to be?
		# Good fucking question. It starts here:
		#   https://github.com/korfuri/django-prometheus/issues/271
		# I can't push new metrics to the Prom REGISTRY because our extension overrides it
		#
		# >Alright, so what about using set_function() on your Gauges?
		# Doesn't work in multiprocess mode
		#
		# >Okay, but how about we let Gunicorn handle it?
		# Threading model is not only complicated, but we'd get one stat collector thread per worker thread, which is "suboptimal"
		#
		# >And you can't put this in the cron container?
		# Nope. PROMETHEUS_MULTIPROC_DIR can't be shared between containers because it has to be ephemeral. It must be wiped every
		# time the app starts or the exporter misbehaves in weird ways.
		#
		# >Jesus Christ
		# Yeah
		#
		(
		set +e
		while true; do
			# This should run forever, but we restart just in case
			python3 manage.py collect-metrics
			sleep 1
		done
		) &
		(
		set +e
		while true; do
			python3 -m gunicorn \
				--bind 0.0.0.0:8080 \
				--workers "${GUNCAD_GUNICORN_WORKERS:-8}" \
				--access-logfile - \
				--access-logformat '%(t)s %({X-Forwarded-For}i)s %(l)s %(h)s %(l)s %(m)s %(s)s %(b)s %(l)s "%(r)s" "%(f)s" "%(a)s" in %(M)sms' \
				--timeout 25 \
				--max-requests 1000 \
				--max-requests-jitter 100 \
				$extraargs \
				guncadindex.wsgi:application
			if [ -n "$GUNCAD_DEBUG" ]; then
				echo "Gunicorn died! Restarting..."
				sleep 1
				rm -rf "${PROMETHEUS_MULTIPROC_DIR:-/dir/that/doesnt/exist/just/in/case}"/*
			else
				echo "Gunicorn died, but we're not in debug! Bailing!"
				exit 1
			fi
		done
		)
		;;
	*)
		# No args, so we complain and explode
		echo "No argument specified -- tell this container what to start (one of lbrynet, gunicorn, cron)"
		echo "Supplied args: $@"
		exit 1
		;;
esac
