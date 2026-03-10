from agegate.utils import AGE_GATE_COOKIE_NAME
from django.test import TestCase
from django.urls import reverse


class AgeGateViewTests(TestCase):
    def test_sets_cookie_and_redirects(self):
        url = reverse("agegate") + "?next=/foo/"
        response = self.client.post(url)

        assert response.status_code == 302
        assert response["Location"] == "/foo/"
        assert AGE_GATE_COOKIE_NAME in response.cookies

    def test_rejects_external_next(self):
        url = reverse("agegate") + "?next=https://evil.com/"
        response = self.client.post(url)

        assert response.status_code == 302
        assert response["Location"] == "/"
