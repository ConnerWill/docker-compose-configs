manage="./manage.py"
[ -e "$manage" ] || {
	echo "Could not find manage.py -- make sure you're in the root of the repo"
	exit 1
}
python3 "$manage" makemigrations
python3 "$manage" lintmigrations
