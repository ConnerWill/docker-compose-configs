from django.urls import include, path
from rest_framework import routers

from . import views
from .feeds import OdyseeReleaseAtomFeed, OdyseeReleaseRSSFeed

router = routers.DefaultRouter()
router.register(r"releases", views.OdyseeReleaseViewSet)
router.register(r"channels", views.OdyseeChannelViewSet)
router.register(r"tags", views.TagViewSet)
router.register(r"taggingrules", views.TaggingRuleViewSet)

urlpatterns = [
    # Landing page
    path("", views.LandingView.as_view(), name="landing"),
    # Discovery view
    path("discover", views.DiscoverView.as_view(), name="discover"),
    # Views for browsing and details of objects
    path("search", views.OdyseeReleaseListView.as_view(), name="listreleases"),
    path(
        "search/advanced",
        views.OdyseeReleaseAdvancedSearchView.as_view(),
        name="search-advanced",
    ),
    # Commented the RSS feed out because, frankly, I just like the Atom one more
    # path("search/rss", OdyseeReleaseRSSFeed(), name="listreleases-rss"),
    path("search/atom", OdyseeReleaseAtomFeed(), name="listreleases-atom"),
    path("detail/<str:pk>", views.OdyseeReleaseDetailView.as_view(), name="detail"),
    path(
        "favorites/render/",
        views.OdyseeReleasePartialView.as_view(),
        name="release-partial",
    ),
    # After a lot of research, I found that Django at one point in time had
    # support for just defining some case-insensitive regex that would've
    # worked really well here. Sadly, they deprecated and removed the behavior
    # because case insensitive URLs are bad practice or something????
    #
    # Anyway, I toyed with some other options and came to the conclusion that,
    # since this is a single-character URL, this is the easiest, simplest, best
    # solution to having it be case-insensitive.
    #
    # The view handles matching the slug as lowercase.
    path(
        "s/<slug:shortlink>",
        views.OdyseeReleaseShortlinkView.as_view(),
        name="shortlink",
    ),
    path(
        "S/<slug:shortlink>",
        views.OdyseeReleaseShortlinkView.as_view(),
    ),
    path("about", views.AboutView.as_view(), name="about"),
    # APIs
    path("api/", include(router.urls)),
    # path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]
