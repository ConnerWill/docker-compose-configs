from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings
from onion.middleware import OnionMiddleware


@override_settings(ALLOWED_HOSTS=["example.com", "indexexample.onion"])
class OnionMiddlewareTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_onion_host_marks_request_and_unsets_cookie_secure(self):
        def get_response(_request):
            response = HttpResponse("ok")
            response.set_cookie("sessionid", "x", secure=True)
            response.set_cookie("csrftoken", "y", secure=True)
            return response

        middleware = OnionMiddleware(get_response)
        request = self.factory.get("/", HTTP_HOST="indexexample.onion")

        response = middleware(request)

        assert request.is_onion is True
        assert response.cookies["sessionid"]["secure"] is False
        assert response.cookies["csrftoken"]["secure"] is False

    def test_non_onion_host_cookies_stay_secure(self):
        def get_response(_request):
            response = HttpResponse("ok")
            response.set_cookie("sessionid", "x", secure=True)
            response.set_cookie("csrftoken", "y", secure=True)
            return response

        middleware = OnionMiddleware(get_response)
        request = self.factory.get("/", HTTP_HOST="example.com")

        response = middleware(request)

        assert request.is_onion is False
        assert response.cookies["sessionid"]["secure"] is True
        assert response.cookies["csrftoken"]["secure"] is True
