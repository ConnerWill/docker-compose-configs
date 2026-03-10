from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from odyseescraper.utils import add_release_to_search_tokens


class OdyseeUtilsTests(SimpleTestCase):
    @patch("odyseescraper.utils.add_tokens")
    def test_add_release_to_search_tokens_delegates_with_name_and_popularity(
        self, mock_add_tokens
    ):
        release = SimpleNamespace(name="My Release", popularity=0.75)

        add_release_to_search_tokens(release)

        mock_add_tokens.assert_called_once_with("My Release", 0.75)
