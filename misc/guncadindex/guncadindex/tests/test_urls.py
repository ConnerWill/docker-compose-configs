from django.test import TestCase
from django.urls import NoReverseMatch, get_resolver, reverse


class URLSmokeTests(TestCase):
    def test_named_urls_render(self):
        resolver = get_resolver()
        blacklist = [
            # POST-only endpoints
            "/accounts/logout/",
            "/favorites/render/",
            # Test pages, don't give a shit
            "/tools/csstest",
        ]
        for name, info in resolver.reverse_dict.items():
            if not isinstance(name, str):
                continue
            try:
                url = reverse(name)
            except NoReverseMatch:
                continue
            if url in blacklist:
                continue

            with self.subTest(url=name):
                response = self.client.get(url)
                self.assertLess(
                    response.status_code,
                    500,
                    msg=f"{name} ({url}) failed with {response.status_code}",
                )
