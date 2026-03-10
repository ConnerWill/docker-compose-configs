# Contributing

## Setting Up a Test Instance

Nice and simple:

```
# Replace with the URL to your fork
git clone gitlab.com:guncad-index/index.git
cd index
./contrib/test-docker.sh
```

Then view http://localhost:8080 in your browser. It should bind mount the current directory in and tell Gunicorn to reload on page modifications, so you can preview your changes live. If you see a big banner that warns you that DEBUG is turned on, you did it right.

You'll probably want to install `requirements*.txt` in a venv locally for autocompletion and formatting tools.

## Styling

There's a styling script supplied in `./contrib/reformat.sh`, but the gist of it is:

* All Python code should be formatted with `black`.
* All Python imports should be formatted with `isort` in `black` profile mode.
* Templates should be linted through `djlint` in `django` mode.

CI will enforce this.

Work to put all that into a pyproject.toml would be more than welcome.

## Testing

Right now we have no automated test framework. We should fix that at some point, but for now, testing is on a best-effort basis. Make sure you don't break shit.

## Updating the Changelog

Whenever you make a change, please update the topmost section of the changelog with a description of what you modified. Sections for each version should be in the order "Fixed", "Added", "Changed", "Deprecated", "Removed", and each change note should be prefixed with whichever one of those is appropriate.

## Submitting a Merge Request

All merge requests should target `master`. Branch names should either describe the changeset in the branch or contain an issue number (ex. `fix-41` is okay, `add-lbry-button` is okay, `dev1` is not.)

One feature per merge request, please.

## Communication

We have a Matrix space! Join it here: https://matrix.to/#/#guncad-index:matrix.org

There's a "Development" channel within. If you have any questions, concerns, or just want to hang out and chat, drop by!

## Licensing

By contributing to this project, you agree to license your code to this repository under the terms of the AGPLv3 license.
