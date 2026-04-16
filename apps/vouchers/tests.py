from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from apps.vouchers.utils import fetch_url_bytes, voucher_image_filename_from_url


class VoucherImageFilenameTests(SimpleTestCase):
    def test_filename_from_url_uses_basename(self):
        url = "https://example.com/wp-content/uploads/2025/10/Voucher-2126.png"
        self.assertEqual(voucher_image_filename_from_url(url, "voucher-150-zl"), "Voucher-2126.png")

    def test_filename_fallback_when_path_empty(self):
        url = "https://example.com/"
        self.assertEqual(voucher_image_filename_from_url(url, "my-slug"), "my-slug.png")


class FetchUrlBytesTests(SimpleTestCase):
    @patch("apps.vouchers.utils.requests.get")
    def test_fetch_returns_content(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.content = b"\x89PNG\r\n"
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        out = fetch_url_bytes("https://example.com/img.png")
        self.assertEqual(out, b"\x89PNG\r\n")
        mock_get.assert_called_once()
