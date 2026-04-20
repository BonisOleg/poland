"""Smoke tests for the unified CMS page builder."""

from __future__ import annotations

from io import StringIO

from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.template import Context, Template
from django.test import RequestFactory, TestCase

from apps.cms.models import GalleryItem, PageBlock, RelatedItem
from apps.cms.utils import get_blocks_for, has_blocks
from apps.pages.models import StaticPage


class PageBlockModelTests(TestCase):
    def setUp(self):
        self.page = StaticPage.objects.create(
            title="Test", slug="test", content="<p>hi</p>",
        )

    def test_create_and_order(self):
        ct = ContentType.objects.get_for_model(StaticPage)
        b1 = PageBlock.objects.create(
            content_type=ct, object_id=self.page.pk, kind="text",
            sort_order=2, body="second",
        )
        b2 = PageBlock.objects.create(
            content_type=ct, object_id=self.page.pk, kind="text",
            sort_order=1, body="first",
        )
        ordered = list(get_blocks_for(self.page))
        self.assertEqual([b.pk for b in ordered], [b2.pk, b1.pk])

    def test_has_blocks_only_visible(self):
        ct = ContentType.objects.get_for_model(StaticPage)
        PageBlock.objects.create(
            content_type=ct, object_id=self.page.pk, kind="text",
            body="x", is_visible=False,
        )
        self.assertFalse(has_blocks(self.page))
        PageBlock.objects.create(
            content_type=ct, object_id=self.page.pk, kind="text",
            body="y", is_visible=True,
        )
        self.assertTrue(has_blocks(self.page))


class RenderBlocksTagTests(TestCase):
    def setUp(self):
        self.page = StaticPage.objects.create(
            title="Render", slug="render-test", content="",
        )
        ct = ContentType.objects.get_for_model(StaticPage)
        PageBlock.objects.create(
            content_type=ct, object_id=self.page.pk, kind="text",
            body="<p>Hello world</p>", heading="Sekcja", sort_order=0,
        )
        gallery = PageBlock.objects.create(
            content_type=ct, object_id=self.page.pk, kind="gallery",
            heading="Galeria", sort_order=1,
        )
        GalleryItem.objects.create(
            block=gallery, image_url="https://example.com/a.jpg",
            alt_text="Alt A", sort_order=0,
        )

    def _render(self) -> str:
        request = RequestFactory().get("/")
        tpl = Template("{% load cms_tags %}{% render_blocks page %}")
        return tpl.render(Context({"page": self.page, "request": request}))

    def test_text_block_rendered(self):
        html = self._render()
        self.assertIn("Sekcja", html)
        self.assertIn("Hello world", html)

    def test_gallery_renders_image(self):
        html = self._render()
        self.assertIn("https://example.com/a.jpg", html)
        self.assertIn('alt="Alt A"', html)


class StaticPageTemplateBackcompatTests(TestCase):
    def test_legacy_html_renders_when_flag_off(self):
        page = StaticPage.objects.create(
            title="Legacy", slug="legacy",
            content="<p>OLD HTML</p>", use_block_builder=False,
        )
        resp = self.client.get(page.get_absolute_url())
        self.assertContains(resp, "OLD HTML")

    def test_blocks_render_when_flag_on(self):
        page = StaticPage.objects.create(
            title="Block", slug="block-on",
            content="<p>OLD HTML</p>", use_block_builder=True,
        )
        ct = ContentType.objects.get_for_model(StaticPage)
        PageBlock.objects.create(
            content_type=ct, object_id=page.pk, kind="text",
            body="<p>NEW BLOCK CONTENT</p>",
        )
        resp = self.client.get(page.get_absolute_url())
        self.assertContains(resp, "NEW BLOCK CONTENT")
        self.assertNotContains(resp, "OLD HTML")


class PopulateCommandTests(TestCase):
    def test_idempotent_and_sets_flag(self):
        page = StaticPage.objects.create(
            title="Pop", slug="populate-test",
            content="<h2>S1</h2><p>body</p><img src='https://x/y.jpg' alt='a'>",
        )
        out = StringIO()
        call_command(
            "populate_cms_blocks", "--owners=static", "--slug=populate-test",
            stdout=out,
        )
        page.refresh_from_db()
        self.assertTrue(page.use_block_builder)
        first_count = PageBlock.objects.filter(
            content_type=ContentType.objects.get_for_model(StaticPage),
            object_id=page.pk,
        ).count()
        self.assertGreaterEqual(first_count, 1)

        # second run is a no-op
        call_command("populate_cms_blocks", "--owners=static", "--slug=populate-test", stdout=StringIO())
        second_count = PageBlock.objects.filter(
            content_type=ContentType.objects.get_for_model(StaticPage),
            object_id=page.pk,
        ).count()
        self.assertEqual(first_count, second_count)

    def test_reset_clears_existing(self):
        page = StaticPage.objects.create(
            title="Reset", slug="reset-test", content="<p>body</p>",
        )
        ct = ContentType.objects.get_for_model(StaticPage)
        PageBlock.objects.create(
            content_type=ct, object_id=page.pk, kind="text", body="manual",
        )
        call_command(
            "populate_cms_blocks", "--owners=static", "--slug=reset-test",
            "--reset", stdout=StringIO(),
        )
        bodies = list(PageBlock.objects.filter(
            content_type=ct, object_id=page.pk
        ).values_list("body", flat=True))
        self.assertNotIn("manual", bodies)


class SetupRolesCommandTests(TestCase):
    def test_creates_groups_with_perms(self):
        call_command("setup_cms_roles", stdout=StringIO())
        cm = Group.objects.get(name="ContentManager")
        mod = Group.objects.get(name="Moderator")
        self.assertGreater(cm.permissions.count(), 0)
        self.assertGreater(mod.permissions.count(), 0)
        # Idempotent — re-running keeps the same set
        before = cm.permissions.count()
        call_command("setup_cms_roles", stdout=StringIO())
        self.assertEqual(before, Group.objects.get(name="ContentManager").permissions.count())


class RelatedItemTests(TestCase):
    def test_manual_related_resolves_to_owner(self):
        from apps.cms.utils import resolve_related_targets

        owner = StaticPage.objects.create(title="Owner", slug="owner-x", content="")
        target = StaticPage.objects.create(title="Target", slug="target-x", content="")
        ct_owner = ContentType.objects.get_for_model(StaticPage)
        block = PageBlock.objects.create(
            content_type=ct_owner, object_id=owner.pk, kind="related",
            related_strategy="manual",
        )
        RelatedItem.objects.create(
            block=block,
            target_content_type=ct_owner,
            target_object_id=target.pk,
        )
        resolved = resolve_related_targets(list(block.related_items.all()))
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].pk, target.pk)
