#!/bin/bash
# We should never have this on while running tests
unset GUNCAD_DEBUG
coverage run ./manage.py test && coverage report
