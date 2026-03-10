from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

from didyoumean.utils import (
    MAXIMUM_TOKEN_LENGTH,
    add_tokens,
    get_correction,
    remove_punctuation,
    tokenize,
    validate_token,
)
from django.test import SimpleTestCase


class DidYouMeanUtilsTests(SimpleTestCase):
    def test_tokenize_lowercases_and_splits(self):
        assert tokenize("Foo BAR baz") == ["foo", "bar", "baz"]

    def test_remove_punctuation(self):
        assert remove_punctuation('"hello,world!"') == "helloworld"

    def test_validate_token_rejects_bad_tokens(self):
        assert validate_token("42") is False
        assert validate_token("-suppressed") is False
        assert validate_token("aa") is False
        assert validate_token("a" * (MAXIMUM_TOKEN_LENGTH + 1)) is False
        assert validate_token("aaaaaa") is False
        assert validate_token("the") is False

    def test_validate_token_accepts_normal_token(self):
        assert validate_token("receiver") is True

    @patch("didyoumean.utils.SearchToken.objects.closest")
    def test_get_correction_keeps_quotes_and_invalid_tokens(self, mock_closest):
        def closest_side_effect(token):
            mapping = {
                '"rifel"': SimpleNamespace(token="rifle"),
                "jig": SimpleNamespace(token="jig"),
            }
            return SimpleNamespace(first=lambda: mapping.get(token))

        mock_closest.side_effect = closest_side_effect
        original, corrected = get_correction('"rifel" 42 jig')

        assert original == '"rifel" 42 jig'
        assert corrected == '"rifle" 42 jig'

    @patch("didyoumean.utils.SearchToken.objects.get_or_create")
    def test_add_tokens_adds_and_updates_popularity(self, mock_get_or_create):
        existing = SimpleNamespace(popularity=0.2, save=MagicMock())
        mock_get_or_create.side_effect = [
            (SimpleNamespace(popularity=0.5, save=MagicMock()), True),
            (existing, False),
        ]

        added = add_tokens("fresh stale!", popularity=0.8)

        assert added == 1
        assert mock_get_or_create.call_args_list == [
            call(token="fresh", defaults={"popularity": 0.8}),
            call(token="stale", defaults={"popularity": 0.8}),
        ]
        assert existing.popularity == 0.8
        existing.save.assert_called_once_with(update_fields=["popularity"])
