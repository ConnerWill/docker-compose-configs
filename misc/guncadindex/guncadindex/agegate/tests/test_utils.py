from agegate.utils import (
    AGE_GATE_COOKIE_AGE,
    AGE_GATE_COOKIE_NAME,
    AGE_GATE_COOKIE_SALT,
    has_valid_disclaimer,
)
from django.core import signing
from django.test import RequestFactory, TestCase


class DisclaimerUtilsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_no_cookie(self):
        request = self.factory.get("/")
        assert has_valid_disclaimer(request) is False

    def test_invalid_cookie(self):
        request = self.factory.get("/")
        request.COOKIES[AGE_GATE_COOKIE_NAME] = "lolno"
        assert has_valid_disclaimer(request) is False

    def test_valid_cookie(self):
        signed = signing.dumps({"accepted": True}, salt=AGE_GATE_COOKIE_SALT)
        request = self.factory.get("/")
        request.COOKIES[AGE_GATE_COOKIE_NAME] = signed
        assert has_valid_disclaimer(request) is True
