# GunCAD Index Administrator's Manual

GunCAD Index is built on top of [Django](https://www.djangoproject.com/), a Python framework for creating websites.

For basic administration, knowledge of Django is **not required**. Advanced administrators are encouraged to aqcuaint themselves with the documentation for that project as a baseline, chiefly that most administration will be done by invoking `manage.py` and how the admin dash works.

## Quickstart

Just wanna get up and running fast? See here:

* [`quickstart.md`](./quickstart.md)
  * Shows how to get a small instance that works for most people up fast

## Tutorials

* [`adding-admin.md`](./adding-admin.md)
  * Shows how to add an administrative user
* [`adding-channels.md`](./adding-channels.md)
  * Shows how to add OdyseeChannels via the admin UI
* [`adding-tags-advanced.md`](./adding-tags-advanced.md)
  * Shows how to manually import a set of Tags and TaggingRules from a YAML file

## Reference Guides

* [`deployment.md`](./deployment.md)
  * Contains detailed deployment information, including a comprehensive list of all configuration envvars, useful volume mounts, alternative setups and topologies, and more
