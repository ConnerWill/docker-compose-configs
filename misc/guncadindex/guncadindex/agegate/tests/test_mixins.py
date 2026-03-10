from agegate.mixins import AgeGateRequiredMixin
from agegate.utils import AGE_GATE_COOKIE_NAME, generate_age_gate_cookie
from django.core import signing
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.views import View


class DummyView(AgeGateRequiredMixin, View):
    def get(self, request):
        return HttpResponse("ok")


class AgeGateMixinTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _request(self, classifier="human"):
        request = self.factory.get("/foo/")
        request.traffic_classifier = classifier
        return request

    def test_bot_not_gated(self):
        request = self._request("bot_google")
        response = DummyView.as_view()(request)
        assert response.status_code == 200

    def test_human_without_cookie_redirected(self):
        request = self._request("human")
        response = DummyView.as_view()(request)
        assert response.status_code == 302
        assert "gate" in response["Location"]

    def test_human_with_cookie_allowed(self):
        signed = generate_age_gate_cookie()
        request = self._request("human")
        request.COOKIES[AGE_GATE_COOKIE_NAME] = signed
        response = DummyView.as_view()(request)
        assert response.status_code == 200

    def test_head_not_gated(self):
        request = self.factory.head("/foo/")
        request.traffic_classifier = "human"
        response = DummyView.as_view()(request)
        assert response.status_code == 200

    def test_googlebot_can_crawl(self):
        request = self.factory.get("/foo/")
        request.traffic_classifier = "bot_google"
        response = DummyView.as_view()(request)
        assert response.status_code == 200
