from unittest.mock import call, patch

from django.test import SimpleTestCase
from vendors.utils import clear_caches


class VendorsUtilsTests(SimpleTestCase):
    @patch("vendors.utils.cache.delete")
    def test_clear_caches_deletes_expected_keys(self, mock_delete):
        clear_caches()

        assert mock_delete.call_args_list == [
            call("vendors_footer"),
            call("should_render_extra_vendors"),
        ]
