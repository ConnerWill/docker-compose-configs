from django.conf import settings


class OnionMiddleware:
    """
    Dynamically sets some Django settings for onion links
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.get_host().endswith(".onion"):
            request.is_onion = True
        else:
            request.is_onion = False

        response = self.get_response(request)

        if getattr(request, "is_onion", False):
            if "sessionid" in response.cookies:
                response.cookies["sessionid"]["secure"] = False
            if "csrftoken" in response.cookies:
                response.cookies["csrftoken"]["secure"] = False

        return response
