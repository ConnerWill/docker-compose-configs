import os
import platform
import sys
from pathlib import Path

import iptools
from django.conf.locale.en import formats as en_formats


# Tiny helper functions
def str_to_bool(value) -> bool:
    """
    Takes a string and returns whether that string should be considered truthy or not
    """
    if isinstance(value, bool):
        return value
    result = value.strip().lower() in ("1", "true", "t", "yes", "on", "enabled")
    return result


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(os.getenv("GUNCAD_DEBUG", False))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    "GUNCAD_SECRET_KEY",
    "django-insecure-v_pp7(w$do^6(!l!@4aorxle#h__igswy)1x#jphy&uj4h0vj_",
)
if not DEBUG and SECRET_KEY.startswith("changeme-"):
    raise RuntimeError(
        "Refusing to start with default GUNCAD_SECRET_KEY -- please set this to a strong random value"
    )

# SECURITY WARNING: set this to your reverse proxy
ALLOWED_HOSTS = ["127.0.0.100"] + os.environ.get("GUNCAD_ALLOWED_HOSTS", "").split(",")
if DEBUG:
    ALLOWED_HOSTS += ["localhost", "localhost.onion", "127.0.0.1"]
    INTERNAL_IPS = iptools.IpRangeList(
        "127.0.0.0/8", "192.168.0.0/16", "172.16.0.0/12", "10.0.0.0/8"
    )

# Weird oneoff settings
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

# Application definition
INSTALLED_APPS = [
    # Metrics
    "django_prometheus",
    # Styling
    "heroicons",
    "compressor",
    "markdownify.apps.MarkdownifyConfig",
    # Dependencies
    "rest_framework",
    "django_migration_linter",
    "storages",
    "health_check",
    # Local apps
    "accounts.apps.AccountsConfig",
    "admintools.apps.AdmintoolsConfig",
    "agegate.apps.AgegateConfig",
    "crowdsource.apps.CrowdsourceConfig",
    "odyseescraper.apps.OdyseescraperConfig",
    "out.apps.OutConfig",
    "releases.apps.ReleasesConfig",
    "legalese.apps.LegaleseConfig",
    "vendors.apps.VendorsConfig",
    "onion.apps.OnionConfig",
    "metrics.apps.MetricsConfig",
    "didyoumean.apps.DidYouMeanConfig",
    "lemmy.apps.LemmyConfig",
    "cf.apps.CloudflareConfig",
    # Base Django stuff
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.humanize",
    "django.contrib.messages",
    "django.contrib.postgres",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    # Must be as low as possible for file integrity
    "django_cleanup.apps.CleanupConfig",
]
MIDDLEWARE = [
    # Before any Prometheus Middleware runs, we run our own
    "metrics.middleware.RequestMiddleware",
    "metrics.middleware.VisitorMiddleware",
    "metrics.middleware.RefererMiddleware",
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    # All middleware needs to sit between the two Prometheus hooks
    "django.middleware.security.SecurityMiddleware",
    # Early hook for this so we don't waste processing time on cucks
    "cf.middleware.CuckStateMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "onion.middleware.OnionMiddleware",
    "cf.middleware.CloudflareTimezoneMiddleware",
    "cf.middleware.CloudflareRegionMiddleware",
    # End Prometheus-monitored hooks
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]
if DEBUG:
    hide_toolbar_patterns = ["/media/", "/static/"]
    # If we're in DEBUG, add debug toolbar support
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
    DEBUG_TOOLBAR_CONFIG = {
        "RESULTS_CACHE_SIZE": 5000,
        "SHOW_TOOLBAR_CALLBACK": lambda request: not any(
            request.path.startswith(p) for p in hide_toolbar_patterns
        ),
    }
    DEBUG_TOOLBAR_PANELS = [
        "debug_toolbar.panels.history.HistoryPanel",
        # "debug_toolbar.panels.versions.VersionsPanel",
        "debug_toolbar.panels.timer.TimerPanel",
        "debug_toolbar.panels.settings.SettingsPanel",
        # "debug_toolbar.panels.headers.HeadersPanel",
        "debug_toolbar.panels.request.RequestPanel",
        "debug_toolbar.panels.sql.SQLPanel",
        # "debug_toolbar.panels.staticfiles.StaticFilesPanel",
        # "debug_toolbar.panels.templates.TemplatesPanel",
        # "debug_toolbar.panels.alerts.AlertsPanel",
        # Has issues with the request classifier middleware
        #'debug_toolbar.panels.cache.CachePanel',
        "debug_toolbar.panels.signals.SignalsPanel",
        # "debug_toolbar.panels.community.CommunityPanel",
        # "debug_toolbar.panels.redirects.RedirectsPanel",
        # "debug_toolbar.panels.profiling.ProfilingPanel",
    ]
ROOT_URLCONF = "guncadindex.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "debug": DEBUG,
            "builtins": [
                "heroicons.templatetags.heroicons",
            ],
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "crowdsource.context_processors.crowdsource",
                "vendors.context_processors.sponsored_vendors",
                "admintools.context_processors.admin_banners",
                "admintools.context_processors.admin_is_debug",
                "agegate.context_processors.age_gate",
            ],
        },
    },
]
WSGI_APPLICATION = "guncadindex.wsgi.application"

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s %(levelname)-8s %(name)s:%(lineno)d: %(message)s",
            "style": "%",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": sys.stdout,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("GUNCAD_DB_NAME", "django"),
        "USER": os.getenv("GUNCAD_DB_USER", "django"),
        "PASSWORD": os.getenv("GUNCAD_DB_PASS", ""),
        "HOST": os.getenv("GUNCAD_DB_HOST", "db"),
        "PORT": os.getenv("GUNCAD_DB_PORT", "5432"),
        "DISABLE_SERVER_SIDE_CURSORS": True,  # Required for PgBouncer
    }
}

# Caching
CACHE_BACKEND = os.getenv("GUNCAD_CACHE_BACKEND", "").lower()

if CACHE_BACKEND in ["redis", "valkey"]:
    REDIS_HOST = os.getenv("GUNCAD_CACHE_REDIS_HOST", "valkey")
    REDIS_PORT = os.getenv("GUNCAD_CACHE_REDIS_PORT", "6379")
    REDIS_DB = os.getenv("GUNCAD_CACHE_REDIS_DB", "0")
    REDIS_PASSWORD = os.getenv("GUNCAD_CACHE_REDIS_PASSWORD", "")

    REDIS_URL = f"redis://{f':{REDIS_PASSWORD}@' if REDIS_PASSWORD else ''}{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

    CACHES = {
        "default": {
            "BACKEND": "django_prometheus.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
        }
    }
else:
    # Fall back to LocMemCache
    CACHES = {
        "default": {
            "BACKEND": "django_prometheus.cache.backends.locmem.LocMemCache",
            "LOCATION": "guncad-locmem",
        }
    }

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Third-party app settings
# djangorestframework
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    "DEFAULT_FILTER_BACKENDS": (),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 25,
}

MARKDOWNIFY = {
    "default": {
        "STRIP": True,
        "MARKDOWN_EXTENSIONS": ["nl2br", "sane_lists", "fenced_code"],
        "WHITELIST_TAGS": [
            "a",
            "abbr",
            "acronym",
            "b",
            "blockquote",
            "br",
            "code",
            "em",
            "h1",
            "h2",
            "h3",
            "i",
            "li",
            "ol",
            "p",
            "pre",
            "strong",
            "ul",
        ],
    },
    "lemmy-comment": {
        "STRIP": True,
        "WHITELIST_TAGS": [
            "abbr",
            "acronym",
            "b",
            "blockquote",
            "em",
            "i",
            "li",
            "ol",
            "p",
            "strong",
            "ul",
        ],
    },
}

SILENCED_SYSTEM_CHECKS = [
    # Under the intended architecture of this app, these errors pertain to the
    # reverse proxy sitting in front of it. They are thus irrelevant
    "security.W004",  # HSTS
    "security.W008",  # http -> https redirect
]

MIGRATION_LINTER_OPTIONS = {
    # https://github.com/3YOURMIND/django-migration-linter/blob/main/docs/usage.md
    "sql_analyzer": "postgresql",
    "git_commit_id": "e38a1577511840939b7d8f643b479d474bd441b0",
    "ignore_sqlmigrate_errors": True,  # https://github.com/3YOURMIND/django-migration-linter/issues/289
    "no_cache": True,  # I just got tired of adding the flag by hand
    "quiet": ["ok", "ignore"],
    "exclude_apps": [
        # These are apps we don't control, sadly
        "sites",
    ],
}

# Internationalization and localization
# https://docs.djangoproject.com/en/5.1/topics/i18n/
LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/Chicago"
USE_I18N = True
USE_TZ = True
USE_L10N = True
en_formats.DATETIME_FORMAT = "F j, Y, g:i A"

# Login settings
LOGIN_REDIRECT_URL = "/"

# Prometheus exporter settings
PROMETHEUS_METRIC_NAMESPACE = "guncadindex"

# CSRF
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    CSRF_TRUSTED_ORIGINS = os.environ.get(
        "GUNCAD_CSRF_ORIGINS", "http://localhost"
    ).split(",")

# GunCAD-index specific code
GUNCAD_SITE_NAME = os.getenv("GUNCAD_SITE_NAME", "GunCAD Index")
GUNCAD_SITE_TAGLINE = os.getenv(
    "GUNCAD_SITE_TAGLINE", "Tell the admin to change his settings"
)
GUNCAD_SITE_WARNING_BANNER = os.getenv("GUNCAD_SITE_WARNING_BANNER", "")
GUNCAD_TRACK_UPDATES = str_to_bool(os.getenv("GUNCAD_TRACK_UPDATES", True))
GUNCAD_TRACK_ODYSEE = str_to_bool(os.getenv("GUNCAD_TRACK_ODYSEE", True))
GUNCAD_LBRYNET_URL = os.getenv("GUNCAD_LBRYNET_URL", r"http://lbrynet:5279")
GUNCAD_GIT_URL = os.getenv("GUNCAD_GIT_URL", "https://gitlab.com/guncad-index/index")
GUNCAD_NODE_NAME = os.getenv("GUNCAD_NODE_NAME", platform.node())
GUNCAD_COMMIT_REF = os.getenv("GUNCAD_COMMIT_REF", "unset")
GUNCAD_HTTPS = str_to_bool(os.getenv("GUNCAD_HTTPS", False))
if GUNCAD_HTTPS:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Admin contact info
GUNCAD_ADMIN_CONTACT = os.getenv("GUNCAD_ADMIN_CONTACT", "")
GUNCAD_ADMIN_TWITTER = os.getenv("GUNCAD_ADMIN_TWITTER", "")
GUNCAD_ADMIN_DONATIONS = os.getenv("GUNCAD_ADMIN_DONATIONS", "")
GUNCAD_ADMIN_BTC = os.getenv("GUNCAD_ADMIN_BTC", "")
GUNCAD_ADMIN_MONERO = os.getenv("GUNCAD_ADMIN_MONERO", "")
GUNCAD_ADMIN_CHAT = os.getenv("GUNCAD_ADMIN_CHAT", "")

# Lemmy support
GUNCAD_LEMMY_INSTANCE = os.getenv("GUNCAD_LEMMY_INSTANCE", None)
GUNCAD_LEMMY_INSTANCE_ENDPOINT = os.getenv("GUNCAD_LEMMY_INSTANCE_ENDPOINT", "/api/v3")
GUNCAD_LEMMY_INSTANCE_WHITELIST = os.getenv(
    "GUNCAD_LEMMY_INSTANCE_WHITELIST", "forum.guncadindex.com,fosscad.io"
).split(",")
GUNCAD_LEMMY_LEMMYVERSE_URL = os.getenv(
    "GUNCAD_LEMMY_LEMMYVERSE_URL", "https://lemmyverse.link"
)
GUNCAD_LEMMY_STATS_URL = os.getenv("GUNCAD_LEMMY_STATS_URL", None)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/
# Staticfiles are always local. This is required for compressor
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
]
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
if os.getenv("GUNCAD_IN_DOCKER"):
    # Use precompiled assets in prod, working dir in dev
    if DEBUG:
        STATIC_ROOT = "/data/static"
    else:
        STATIC_ROOT = "/static"
        COMPRESS_ENABLED = True
        COMPRESS_OFFLINE = True
else:
    STATIC_ROOT = "data/static/"
STATIC_URL = "static/"
COMPRESS_PRECOMPILERS = (("text/x-scss", "django_libsass.SassCompiler"),)
# But media? Media can be on S3
GUNCAD_S3_ENABLED = bool(os.getenv("GUNCAD_S3_ENABLED"))
if GUNCAD_S3_ENABLED:
    # Maps Index envvars to specific boto expectations
    AWS_ACCESS_KEY_ID = os.getenv("GUNCAD_S3_ACCESS_KEY")
    AWS_SECRET_ACCESS_KEY = os.getenv("GUNCAD_S3_SECRET_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("GUNCAD_S3_BUCKET_NAME")
    AWS_S3_ENDPOINT_URL = os.getenv("GUNCAD_S3_ENDPOINT_URL")
    AWS_S3_REGION_NAME = os.getenv(
        "GUNCAD_S3_REGION_NAME",
        "us-east-1",
    )
    AWS_S3_SIGNATURE_VERSION = "s3v4"
    AWS_S3_ADDRESSING_STYLE = "virtual"

    AWS_QUERYSTRING_AUTH = False
    AWS_DEFAULT_ACL = None
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": "max-age=31536000, public",
    }
    # Fail fast if we're misconfigured
    required = [
        AWS_ACCESS_KEY_ID,
        AWS_SECRET_ACCESS_KEY,
        AWS_STORAGE_BUCKET_NAME,
        AWS_S3_ENDPOINT_URL,
    ]
    if not all(required):
        raise RuntimeError(
            "GUNCAD_S3_ENABLED is set but required S3 environment variables are missing"
        )
    # Set storage backends
    STORAGES = {
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
        "default": {
            "BACKEND": "admintools.storage.MediaStorage",
            "OPTIONS": {
                "location": "media",
                "file_overwrite": False,
            },
        },
    }
    # URLs point directly to the bucket (or are proxied through the cloud)
    AWS_S3_CUSTOM_DOMAIN = os.getenv("GUNCAD_S3_CUSTOM_DOMAIN")
    if AWS_S3_CUSTOM_DOMAIN:
        MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/media/"
    else:
        base = AWS_S3_ENDPOINT_URL.rstrip("/")
        MEDIA_URL = f"{base}/{AWS_STORAGE_BUCKET_NAME}/media/"
else:
    MEDIA_URL = "media/"
# Unscoped because it's used during migration
MEDIA_ROOT = "/data/media" if os.getenv("GUNCAD_IN_DOCKER") else "data/media/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
