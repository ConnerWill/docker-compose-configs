from admintools.sitemaps import AdminNavbarLinkSitemap
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps import Sitemap
from django.contrib.sitemaps.views import sitemap
from django.contrib.staticfiles.storage import staticfiles_storage
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from django.views.decorators.cache import cache_page
from django.views.defaults import (
    bad_request,
    page_not_found,
    permission_denied,
    server_error,
)
from django.views.generic.base import RedirectView, TemplateView
from health_check.views import HealthCheckView
from legalese.sitemaps import LegaleseSitemap
from odyseescraper.sitemaps import OdyseeReleaseRecentSitemap

sitemaps = {
    "navbar_links": AdminNavbarLinkSitemap,
    "latest": OdyseeReleaseRecentSitemap,
    "legal": LegaleseSitemap,
}

urlpatterns = [
    path(
        "healthz",
        HealthCheckView.as_view(
            checks=[
                "health_check.Cache",
                "health_check.Database",
            ]
        ),
        name="healthz",
    ),
    path("", include("odyseescraper.urls")),
    path("", include("legalese.urls")),
    path("", include("django_prometheus.urls")),
    path("accounts/", include("accounts.urls")),
    path("vote/", include("crowdsource.urls")),
    path("tools/", include("admintools.urls")),
    path("out/", include("out.urls")),
    path("gate/", include("agegate.urls")),
    path("cf/", include("cf.urls")),
    path("vendors/", include("vendors.urls")),
    path(
        "favicon.ico",
        RedirectView.as_view(url=staticfiles_storage.url("generated/favicon.ico")),
    ),
    path("admin/", admin.site.urls),
    path(
        "sitemap.xml",
        cache_page(86400)(sitemap),
        {"sitemaps": sitemaps},
        name="sitemap",
    ),
    path(
        "opensearch.xml",
        TemplateView.as_view(
            template_name="opensearch.xml",
            content_type="application/opensearchdescription+xml",
        ),
        name="opensearch.xml",
    ),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
]

if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns += [
        path("400/", bad_request, kwargs={"exception": Exception("Bad Request!")}),
        path(
            "403/",
            permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path("404/", page_not_found, kwargs={"exception": Exception("Page not Found")}),
        path("500/", server_error),
    ]
    urlpatterns += debug_toolbar_urls()
    # This is so, if you turn debug mode on, gunicorn will serve statics
    # If you rely on this in prod I'll chop your fucking kneecaps off
    urlpatterns += staticfiles_urlpatterns()
    if not getattr(settings, "GUNCAD_S3_ENABLED", False):
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
