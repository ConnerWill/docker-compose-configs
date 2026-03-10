from django.core.cache import cache
from django.test import RequestFactory, TestCase, override_settings

from .middleware import RequestMiddleware
from .models import TrafficClassifier


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
)
class RequestMiddlewareTestCase(TestCase):
    def setUp(self):
        TrafficClassifier.objects.create(
            priority=100,
            kind="user_agent",
            pattern="Firefox",
            value="human_firefox_1",
            description="Firefox 1",
        )
        TrafficClassifier.objects.create(
            priority=100,
            kind="user_agent",
            pattern="Firefox",
            value="human_firefox_2",
            description="Firefox 2",
        )
        TrafficClassifier.objects.create(
            priority=50,
            kind="referer",
            pattern=":empty:",
            value="bot",
            description="All remaining no-referers should be bots",
        )
        TrafficClassifier.objects.create(
            priority=1000,
            kind="path",
            pattern="/api",
            value="api",
            description="API access trumps all",
        )
        self.factory = RequestFactory()
        self.middleware = RequestMiddleware(get_response=lambda req: None)

    def test_rule_order(self):
        # Do the rules loaded by the middleware make sense?
        rules = self.middleware.load_rules()
        self.assertGreater(len(rules), 1)
        rule1 = rules[0]
        rule2 = rules[1]
        self.assertGreater(rule1.get("priority"), rule2.get("priority"))

    def test_match_rule_function(self):
        # Basic string comp tests
        self.assertTrue(self.middleware.match_rule("foo", "foo"))
        self.assertTrue(self.middleware.match_rule("foo", "foobar"))
        self.assertFalse(self.middleware.match_rule("foo", "bar"))
        # Casing
        self.assertTrue(self.middleware.match_rule("Firefox", "Firefox"))
        self.assertTrue(self.middleware.match_rule("firefox", "Firefox"))
        self.assertTrue(self.middleware.match_rule("Firefox", "firefox"))
        # Partial matching
        self.assertTrue(self.middleware.match_rule("/api", "/api/somepath"))
        self.assertFalse(self.middleware.match_rule("/detail", "/api"))
        # Special cases
        self.assertTrue(self.middleware.match_rule(":empty:", ""))

    def test_match_api(self):
        request = self.factory.get("/api")
        self.middleware(request)
        self.assertEqual(request.traffic_classifier, "api")

    def test_match_human(self):
        request = self.factory.get("/", **{"HTTP_USER_AGENT": "Firefox"})
        self.middleware(request)
        # Seeing the 1st one means we have bad rules ordering
        self.assertEqual(request.traffic_classifier, "human_firefox_2")

    def test_match_empty(self):
        # Does a request with no host header match the empty rule?
        request = self.factory.get("/")
        cache.clear()
        self.middleware(request)
        self.assertEqual(request.traffic_classifier, "bot")
