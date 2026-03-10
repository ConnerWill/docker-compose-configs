from io import StringIO

from django.conf import settings
from django.core.cache import cache
from django.core.management import call_command
from django.test import RequestFactory, TestCase

from .context_processors import admin_banners, admin_is_debug
from .models import AdminNavbarLink, AdminSiteBanner


class AdminCommandTestCase(TestCase):
    def test_get_cache_all(self):
        out = StringIO()
        call_command("getcache", stdout=out)
        self.assertIn("backend does not support iteration", out.getvalue())

    def test_get_cache(self):
        cache.set("test_get_cache", "asdf")
        self.assertEqual(cache.get("test_get_cache"), "asdf")

        out = StringIO()
        call_command("getcache", "test_get_cache", stdout=out)

        self.assertIn("asdf", out.getvalue())

    def test_get_cache_missing(self):
        cache.clear()
        out = StringIO()

        call_command("getcache", "somekey", stdout=out)

        self.assertIn("No value found", out.getvalue())

    def test_clear_cache(self):
        cache.set("test_clear_cache", "foobar")
        self.assertEqual(cache.get("test_clear_cache"), "foobar")

        out = StringIO()
        call_command("clearcache", stdout=out)

        self.assertIsNone(cache.get("test_clear_cache"))
        self.assertIn("Cache cleared", out.getvalue())


class AdminContextProcessorTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_admin_navbar_links(self):
        badlink = AdminNavbarLink.objects.create(
            visible=False, text="Bad Link", link="https://example.com/badlink"
        )
        goodlink = AdminNavbarLink.objects.create(
            visible=True, text="Good Link", link="https://example.com/goodlink"
        )
        cache.clear()
        request = self.factory.get("/")
        context = admin_banners(request)

        self.assertIn(
            str(goodlink.id), context["admin_navbar_links"].values_list("id", flat=True)
        )
        self.assertNotIn(
            str(badlink.id), context["admin_navbar_links"].values_list("id", flat=True)
        )

    def test_default_navbar_links(self):
        defaults = [
            "000-home",
            "000-browse",
            "000-discover",
            "000-learn",
            "000-wiki",
            "000-about",
        ]
        request = self.factory.get("/")
        context = admin_banners(request)
        for link in defaults:
            self.assertIn(
                link, context["admin_navbar_links"].values_list("id", flat=True)
            )

    def test_admin_is_debug(self):
        request = self.factory.get("/")
        context = admin_is_debug(request)
        self.assertEqual(context["is_debug"], settings.DEBUG)
