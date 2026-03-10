# Adding an Administrative User

It's pretty straightforward. This guide will assume you're using Docker -- if you aren't, just invoke `./manage.py` the way you normally would.

## Log Into the Container

Jump into the container via `docker exec` (or `podman exec` if you're using Podman):

```
# docker exec -it my-container /bin/bash
root@3dce5c6dfce0:/app#
```

## Create the User

Issue this command and follow the prompts:

```
docker# ./manage.py createsuperuser
```

**NOTE**: You should be very careful to give the admin a unique, strong name and password.

You can then log in via the "Log In" link at the bottom of each page.
