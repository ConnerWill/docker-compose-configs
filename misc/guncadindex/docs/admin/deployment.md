# Deployment

## Overview

The stock `docker-compose.yml` contains everything you need to run the Index **except** for a reverse proxy. Here's the rundown:

* Containers
  * `guncad-index`
    * The main Gunicorn container. Serves web requests
    * Does **not** serve static files. Read on
  * `cron`
    * Runs scheduled jobs in the background, like polling for releases and managing tagging
  * `lbrynet`
    * Allows the Index (specifically `cron`) to analyze the LBRY blockchain. Required for any amount of useful work
  * `valkey`
    * Object cache. Can be replaced with Redis if your heart desires it
  * `db`
    * PostgreSQL, version 14 or higher
* Volumes (see "Volumes" section for details)
  * `gci-data`
    * Contains site data
  * `gci-lbry-data`
    * Contains cached blockchain state

You will also need to configure a reverse proxy such as nginx as part of setup. Since there are a large number of those in a wide variety, implementation will be left as an exercise for the reader. The important parts, however, are:

1. You **must** proxy `guncad-index` through. The container hosts the webserver on `:8080/tcp`
2. You **must** serve `gci-data:/static` (`/data/static` as mounted in the containers) at `/static` for any of the site's assets to work at all (unless you use S3, but you'll know what you're doing in that case)

### Maintenance Page

As part of the stock website bundle, `/static/maintenance.html` is a static webpage that auto-refreshes which can be used as an error page, should you so desire. You'll have to manually edit the links in there -- it's not rendered by Django at all.

## Database Requirements

PostgreSQL is required, version 14 or higher. Installation will add the `pg_trgm` extension -- in versions below 13, this will fail unless the DB user is privileged (don't do that).

## Configuration Variables

The following environment variables should be set to configure the application:

| Environment Variable | Description | Default Value |
| -------------------- | ----------- | ------------- |
| `GUNCAD_DEBUG`       | **Turn this off in a production environment**. Sets the Django `DEBUG` variable. | None |
| `GUNCAD_HTTPS`       | Set to a truthy value if you intend to serve the site over HTTPS. This enables several HTTPS-only security features | None |
| `GUNCAD_ALLOWED_HOSTS` | **MUST** be set. Should be a comma-separated list of hosts that are allowed to see the site. [See here](https://docs.djangoproject.com/en/5.1/ref/settings/#allowed-hosts). Probably just need to set the name you're hosting on. | None (and if DEBUG is on it's ignored) |
| `GUNCAD_CSRF_ORIGINS`  | **MUST** be set. Should be a comma-separated list of URLs (with `http`/`https`!) that are allowed to submit "dangerous" requests. [See here](https://docs.djangoproject.com/en/5.1/ref/settings/#csrf-trusted-origins). Probably just need the URL you're hosting on. | None (and ignored in DEBUG) |
| `GUNCAD_SECRET_KEY`    | **MUST** be set. Used for certain secure features, but not to salt anything in the database | None |
| `GUNCAD_SITE_NAME`     | The user-friendly name of this index | `GunCAD Index` |
| `GUNCAD_SITE_TAGLINE`  | A user-friendly tagline for this index | `Tell the admin to change his settings` |
| `GUNCAD_SITE_WARNING_BANNER` | A banner to display across the top of the site. Use this if you have something important to say to your users or want to flag down a test instance | None |
| `GUNCAD_GUNICORN_WORKERS` | How many workers gunicorn should spawn. Bump up if you don't have enough workers to meet demand | 8 |
| `GUNCAD_LBRYNET_URL` | The URL to the API endpoint of the lbrynet instance we should communicate with. You should only have to change this if you're altering the container name of your LBRY instance or something | `http://lbrynet:5279` |
| `GUNCAD_NODE_NAME` | The hostname this instance should report. Defaults to the system hostname (which is often the container or pod ID) but can be overridden if you want to | None |

Database configuration is as follows. The defaults get you 90% of the way there:

| Environment Variable | Description | Default Value |
| -------------------- | ----------- | ------------- |
| `GUNCAD_DB_USER` | **MUST** be set. Username for connecting to the DB server | `django` |
| `GUNCAD_DB_PASS` | **MUST** be set. Password for connecting to the DB server | Unset |
| `GUNCAD_DB_NAME` | **MUST** be set. Database to connect to | `django` |
| `GUNCAD_DB_HOST` | **MUST** be set. Host to connect to | `db` (for the compose file) |
| `GUNCAD_DB_PORT` | **MUST** be set. Port to connect to | `5432` |

The standard setup leverages Valkey/Redis, which requires that you set these config vars. If you don't, it'll try to use the standard Django in-memory cache, but *that type of setup is untested* and should *not* be relied on in production:

| Environment Variable | Description | Default Value |
| -------------------- | ----------- | ------------- |
| `GUNCAD_CACHE_BACKEND` | The backend caching system to use. If unset or invalid, defaults to `LocMemCache`, consider setting to `valkey`. | Unset |
| `GUNCAD_CACHE_REDIS_HOST` | The host to use for Redis/Valkey | `valkey` |
| `GUNCAD_CACHE_REDIS_PORT` | The port to use for Redis/Valkey | `6379` |
| `GUNCAD_CACHE_REDIS_DB` | The database index to use | `0` |
| `GUNCAD_CACHE_REDIS_PASSWORD` | Optional. The password to use when connecting to Redis/Valkey | Unset |

Additionally, if you decide you don't want to use local volumes and instead want everything (staticfiles and media) to live in an S3-compatible object store, configure these envvars. This bucket will be used for media files, but will NOT be used for static due to restrictions with other plugins (namely compressor):

> [!note]
> If you're migrating from an existing volume to S3, keep the media volume mounted and invoke `manage.py resave-to-s3` inside the container with the proper envvars set. This will bulk-upload your existing media to S3. This process may take a while.

| Environment Variable | Description | Default Value |
| -------------------- | ----------- | ------------- |
| `GUNCAD_S3_ENABLED` | If set, toggles on the usage of S3 for media | Unset |
| `GUNCAD_S3_ACCESS_KEY` | The access key ID we should use for uploading to S3 | Unset |
| `GUNCAD_S3_SECRET_KEY` | The secret access key we should use for uploading to S3 | Unset |
| `GUNCAD_S3_BUCKET_NAME` | The name of the bucket we'll be using for media. Ex. `guncad-index` | Unset |
| `GUNCAD_S3_ENDPOINT_URL` | The endpoint to talk to. Change if you need to use a non-AWS S3 provider. Ex `https://us-east-1.linodeobjects.com` | Unset |
| `GUNCAD_S3_REGION_NAME` | The region the bucket is located in | `us-east-1` |
| `GUNCAD_S3_CUSTOM_DOMAIN` | Optional custom domain/CDN hostname for serving media (no scheme). Links to assets will point to this domain instead of straight to the bucket, preventing an origin leak. Ex. `cdn.guncadindex.com` | Unset |

It'd be very wise of you to set **at least one of these**, otherwise users can't reach you about things. You can put newlines in this string and they'll show up as breaks in the text. Setting the other options will add buttons to the footer:

| Environment Variable | Description | Default Value |
| -------------------- | ----------- | ------------- |
| `GUNCAD_ADMIN_CONTACT` | A brief blurb about where users can reach you if they have issues. Can be Rocketchat, Matrix, Twitter, whatever. You may also be interested in using one of the targeted links below for fancy buttons | Unset |
| `GUNCAD_ADMIN_TWITTER` | A link to your Twitter account | Unset |
| `GUNCAD_ADMIN_DONATIONS` | A link to your donations page | Unset |
| `GUNCAD_ADMIN_BTC` | A link to somewhere your users can donate Bitcoin | Unset |
| `GUNCAD_ADMIN_MONERO` | A link to somewhere your users can donate Monero | Unset |
| `GUNCAD_ADMIN_CHAT` | A link to a chat application, like Matrix | Unset |

As part of basic behavior, we run a cronjob in a separate container. That cronjob uses these environment variables for configuration:

| Environment Variable | Description | Default Value |
| -------------------- | ----------- | ------------- |
| `GUNCAD_CRON_MINIMUM_DELAY` | How long in seconds we should wait, at minimum, before each cronjob. If this is shorter than the duration of a cron run, it'll skew when the next job fires off (which isn't a big deal) | 3600 |
| `GUNCAD_TRACK_UPDATES` | Whether or not to track updates to releases. Has historically been used to suppress notifications during critical vulnerability triage | True |
| `GUNCAD_TRACK_ODYSEE` | Whether or not to acquire Odysee-specific information about releases. Set to `False` if Odysee ever goes down | True |

If you're interested in monitoring, consider setting a statsd endpoint for Gunicorn to send statistics to (there's a good example in `docker-compose.yml`). I'd also highly recommend [reading this](https://medium.com/@damianmyerscough/monitoring-gunicorn-with-prometheus-789954150069) and [referring to this](https://github.com/blueswen/gunicorn-monitoring) if you like Prometheus more (I sure do):

| Environment Variable | Description | Default Value |
| -------------------- | ----------- | ------------- |
| `GUNCAD_STATSD_HOST` | Host to send stats to | Unset |
| `GUNCAD_STATSD_PORT` | Port to send those stats to on that host | Unset |

If you'd like to use the AI tagging feature, we need your X API key. Support for ollama's coming later:

| Environment Variable | Description | Default Value |
| -------------------- | ----------- | ------------- |
| `GUNCAD_AI_XAI_API_KEY` | Your x.ai API key | Unset |
| `GUNCAD_AI_BATCH_SIZE` | How many releases to tag at each scraping interval. | 100 |
| `GUNCAD_AI_MODEL`    | The model to use. There's a default chosen that's unique per-service-provider that works pretty well, but you can change that by changing this. | Unset |

If you'd like to show Lemmy search results underneath your model, you'll want to set these variables up:

| Environment Variable | Description | Default Value |
| -------------------- | ----------- | ------------- |
| `GUNCAD_LEMMY_INSTANCE` | The instance to hit as a **URL** | Unset |
| `GUNCAD_LEMMY_INSTANCE_ENDPOINT` | The path to the API root. Special value `None` will hit the root of `GUNCAD_LEMMY_INSTANCE` instead (which is very nonstandard) | `/api/v3` |
| `GUNCAD_LEMMY_INSTANCE_WHITELIST` | A comma-separated list of Lemmy instances' domains that we want to display. If unset, no filtering will be done | `forum.guncadindex.com,fosscad.io` |
| `GUNCAD_LEMMY_LEMMYVERSE_URL` | A URL to a `lemmyverse.link`-like service that we can use to render AP IDs agnostic | `https://lemmyverse.link` |

Optionally, if you have your own fork or are mirroring the source code, set this one too:

| Environment Variable | Description | Default Value |
| -------------------- | ----------- | ------------- |
| `GUNCAD_GIT_URL`     | A URL that links to the source code of the instance | Probably wherever you're reading this doc from |

## Volumes

Users not using the docker-compose file may be interested in volumes at the following paths:

| Container | Path | Description |
| --------- | ---- | ----------- |
| `guncad-index`, `cron` | `/data` | **Pretty damn important**. `/data/static` should be served by your reverse proxy at `/static/`. This should be present in all mentioned containers in the leftmost column, otherwise they can't coordinate |
| `lbrynet` | `/home/django/.local/share/lbry` | The status of the local LBRY endpoint. You'll want to cache this, otherwise container rebuilds will require you to download a ton of data |
