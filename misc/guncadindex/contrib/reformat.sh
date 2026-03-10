#! /bin/sh
isort --profile black .
black .
djlint --profile=django --reformat .
./contrib/yamlfmt.sh
