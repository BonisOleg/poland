import os
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import RequestFactory, SimpleTestCase, TestCase

from apps.core.context_processors import global_context


class GlobalContextTests(SimpleTestCase):
    def test_includes_static_asset_version(self):
        request = RequestFactory().get("/")
        ctx = global_context(request)
        self.assertIn("STATIC_ASSET_VERSION", ctx)
        self.assertTrue(ctx["STATIC_ASSET_VERSION"])


class EnsureSuperuserCommandTests(TestCase):
    @patch.dict(
        os.environ,
        {
            "DJANGO_ADMIN_USERNAME": "ensure_superuser_test",
            "DJANGO_ADMIN_PASSWORD": "ensure-superuser-test-pw-1",
        },
        clear=False,
    )
    def test_creates_superuser_from_env(self):
        User = get_user_model()
        self.assertFalse(User.objects.filter(username="ensure_superuser_test").exists())
        call_command("ensure_superuser", stdout=StringIO())
        user = User.objects.get(username="ensure_superuser_test")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.check_password("ensure-superuser-test-pw-1"))

    @patch.dict(
        os.environ,
        {"DJANGO_ADMIN_USERNAME": "", "DJANGO_ADMIN_PASSWORD": ""},
        clear=False,
    )
    def test_defaults_to_admin_credentials(self):
        User = get_user_model()
        call_command("ensure_superuser", stdout=StringIO())
        user = User.objects.get(username="admin")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password("admin"))
