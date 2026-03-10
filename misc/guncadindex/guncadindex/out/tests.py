from unittest.mock import patch

from django.core import signing
from django.core.cache import cache
from django.test import RequestFactory, SimpleTestCase
from out.utils import get_key_for_url, retrieve_outbound_url, store_outbound_url
from out.views import DISCLAIMER_COOKIE_NAME, OutRedirectView


class OutboundUrlUtilsTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def test_get_key_for_url_is_stable(self):
        url = "https://example.org/some/path?q=test"
        first = get_key_for_url(url)
        second = get_key_for_url(url)

        assert first == second
        assert len(first) == 8

    def test_store_and_retrieve_outbound_url(self):
        url = "https://example.org/resource"
        key = store_outbound_url(url)

        assert retrieve_outbound_url(key) == url

    def test_retrieve_outbound_url_missing_returns_none(self):
        assert retrieve_outbound_url("deadbeef") is None


class OutboundRedirectViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch("out.views.utils.retrieve_outbound_url", return_value=None)
    def test_get_with_missing_target_redirects_home(self, _mock_retrieve):
        request = self.factory.get("/out/")
        request.traffic_classifier = "human"

        response = OutRedirectView.as_view()(request)

        assert response.status_code == 302
        assert response["Location"] == "/"

    @patch(
        "out.views.utils.retrieve_outbound_url", return_value="https://example.org/path"
    )
    @patch("out.views.outbound_request_counter.labels")
    def test_get_with_cookie_redirects_to_target(self, mock_labels, _mock_retrieve):
        request = self.factory.get("/out/?t=abc123")
        request.COOKIES[DISCLAIMER_COOKIE_NAME] = signing.dumps(
            {"accepted": True},
            salt="guncad-outbound-disclaimer",
        )
        request.traffic_classifier = "human"

        response = OutRedirectView.as_view()(request)

        assert response.status_code == 302
        assert response["Location"] == "https://example.org/path"
        mock_labels.return_value.inc.assert_called_once()

    @patch(
        "out.views.utils.retrieve_outbound_url", return_value="https://example.org/path"
    )
    @patch("out.views.outbound_request_counter.labels")
    def test_get_without_cookie_renders_warning_page(self, mock_labels, _mock_retrieve):
        request = self.factory.get("/out/?t=abc123")
        request.traffic_classifier = "human"

        response = OutRedirectView.as_view()(request)

        assert response.status_code == 200
        assert response.context_data["target_url"] == "exam******"
        mock_labels.return_value.inc.assert_called_once()

    @patch(
        "out.views.utils.retrieve_outbound_url", return_value="https://example.org/path"
    )
    @patch("out.views.outbound_request_counter.labels")
    def test_get_for_bot_skips_counter(self, mock_labels, _mock_retrieve):
        request = self.factory.get("/out/?t=abc123")
        request.traffic_classifier = "bot_google"

        response = OutRedirectView.as_view()(request)

        assert response.status_code == 200
        mock_labels.assert_not_called()

    @patch(
        "out.views.utils.retrieve_outbound_url", return_value="https://example.org/path"
    )
    @patch("out.views.outbound_request_counter.labels")
    def test_get_with_blocked_region_redirects_home(self, mock_labels, _mock_retrieve):
        request = self.factory.get("/out/?t=abc123")
        request.traffic_classifier = "human"
        request.blocked_region_action = 10

        response = OutRedirectView.as_view()(request)

        assert response.status_code == 302
        assert response["Location"] == "/"
        mock_labels.assert_not_called()

    @patch(
        "out.views.utils.retrieve_outbound_url", return_value="https://example.org/path"
    )
    @patch("out.views.outbound_request_counter.labels")
    def test_get_with_cookie_and_blocked_region_still_redirects_home(
        self, mock_labels, _mock_retrieve
    ):
        request = self.factory.get("/out/?t=abc123")
        request.COOKIES[DISCLAIMER_COOKIE_NAME] = signing.dumps(
            {"accepted": True},
            salt="guncad-outbound-disclaimer",
        )
        request.traffic_classifier = "human"
        request.blocked_region_action = 10

        response = OutRedirectView.as_view()(request)

        assert response.status_code == 302
        assert response["Location"] == "/"
        mock_labels.assert_not_called()

    @patch(
        "out.views.utils.retrieve_outbound_url", return_value="https://example.org/path"
    )
    def test_post_sets_disclaimer_cookie_and_redirects(self, _mock_retrieve):
        request = self.factory.post("/out/?t=abc123")
        request.traffic_classifier = "human"

        response = OutRedirectView.as_view()(request)

        assert response.status_code == 302
        assert response["Location"] == "https://example.org/path"
        assert DISCLAIMER_COOKIE_NAME in response.cookies
