from django.test import RequestFactory, SimpleTestCase

from apps.core.context_processors import global_context


class GlobalContextTests(SimpleTestCase):
    def test_includes_static_asset_version(self):
        request = RequestFactory().get("/")
        ctx = global_context(request)
        self.assertIn("STATIC_ASSET_VERSION", ctx)
        self.assertTrue(ctx["STATIC_ASSET_VERSION"])
