"""Tests for pages app."""

from django.core import mail
from django.test import SimpleTestCase, TestCase, override_settings

from apps.pages.management.commands.clean_elementor_content import transform_html
from apps.pages.models import GroupInquiry
from apps.pages.utils import (
    extract_media_from_html,
    remove_products_grid_from_html,
    split_after_first_vouchery_panel,
    split_html_by_h2_into_panels,
    split_vouchery_content_into_panels,
    strip_elementor_residue,
    strip_quick_view_from_html,
    merge_dla_firm_panel_pairs,
    tag_dla_firm_group_ctas,
    wrap_dla_firm_tickets_word,
    tag_vouchery_faq_section,
    tag_vouchery_offer_section,
    tag_vouchery_reasons_list,
    transform_vouchery_faq_editor_list_to_accordion,
)


class TagVoucheryReasonsListTests(SimpleTestCase):
    def test_adds_class_to_ul_after_5_powodow_h2(self) -> None:
        html = (
            '<h2>5 POWODÓW DLA KTÓRYCH WARTO</h2>'
            "<ul><li>One</li><li>Two</li></ul>"
            '<p><a href="#voucher">PRZEŻYJ</a></p>'
        )
        out = tag_vouchery_reasons_list(html)
        self.assertIn("vouchery-reasons-list", out)
        self.assertIn('<ul class="vouchery-reasons-list">', out)

    def test_converts_paragraphs_to_ul_after_dlaczego_voucher_h2(self) -> None:
        html = (
            "<h2>DLACZEGO VOUCHER JEST DOBRYM POMYSŁEM?</h2>"
            "<p>First point.</p>"
            "<p>Second point.</p>"
            '<p><a href="#voucher">KUP VOUCHER</a></p>'
        )
        out = tag_vouchery_reasons_list(html)
        self.assertIn('class="vouchery-reasons-list"', out)
        self.assertIn("<li>First point.</li>", out)
        self.assertIn("<li>Second point.</li>", out)
        self.assertIn('<p><a href="#voucher">KUP VOUCHER</a></p>', out)


class TagVoucheryOfferElementorTests(SimpleTestCase):
    def test_wraps_following_elementor_widgets_not_only_h2_siblings(self) -> None:
        """Raw Elementor puts <p> in sibling widgets; h2 has no element siblings."""
        html = """
        <div class="elementor-element elementor-widget elementor-widget-heading">
          <div class="elementor-widget-container">
            <h2>CHCESZ ZASKOCZYĆ DZIECI ?</h2>
          </div>
        </div>
        <div class="elementor-element elementor-widget elementor-widget-text-editor">
          <div class="elementor-widget-container"><p>ZAREZERWUJ</p></div>
        </div>
        <div class="elementor-element elementor-widget elementor-widget-button">
          <a class="elementor-button">ZAPYTAJ</a>
        </div>
        """
        out = tag_vouchery_offer_section(html)
        self.assertIn("vouchery-offer-body", out)
        self.assertIn("ZAREZERWUJ", out)
        self.assertIn("ZAPYTAJ", out)


class TagVoucheryFaqSectionTests(SimpleTestCase):
    def test_wraps_body_under_faq_heading(self) -> None:
        html = (
            "<h2>NAJCZĘŚCIEJ ZADAWANE PYTANIA (FAQ)</h2>"
            "<p>Question one? Question two?</p>"
        )
        out = tag_vouchery_faq_section(html)
        self.assertIn("vouchery-faq-section__title", out)
        self.assertIn('class="vouchery-faq-body"', out)
        self.assertIn("Question one", out)


class TransformVoucheryFaqAccordionTests(SimpleTestCase):
    def test_ckeditor_p_ul_pairs_become_details_accordion(self) -> None:
        html = (
            "<h2>NAJCZĘŚCIEJ ZADAWANE PYTANIA (FAQ)</h2>"
            "<p>Jak wygląda dostawa?</p>"
            "<ul><li>Odpowiedź pierwsza.</li></ul>"
            "<p>Drugie pytanie?</p>"
            "<ul><li><p>Druga odpowiedź.</p></li></ul>"
        )
        out = tag_vouchery_faq_section(html)
        out = transform_vouchery_faq_editor_list_to_accordion(out)
        self.assertEqual(out.count('class="content-accordion"'), 1)
        self.assertEqual(out.count("content-accordion__item"), 2)
        self.assertIn("Jak wygląda dostawa?", out)
        self.assertIn("Odpowiedź pierwsza.", out)
        self.assertIn("Drugie pytanie?", out)
        self.assertIn("Druga odpowiedź.", out)
        self.assertNotIn("<ul>", out)

    def test_skips_when_content_accordion_already_present(self) -> None:
        html = (
            '<div class="vouchery-faq-body">'
            '<div class="content-accordion">'
            '<details class="content-accordion__item">'
            '<summary class="content-accordion__title">Q</summary>'
            "<p>A</p>"
            "</details>"
            "</div>"
            "</div>"
        )
        out = transform_vouchery_faq_editor_list_to_accordion(html)
        self.assertEqual(out.count('class="content-accordion"'), 1)

    def test_leaves_orphan_paragraph_when_no_following_ul(self) -> None:
        html = (
            "<h2>NAJCZĘŚCIEJ ZADAWANE PYTANIA (FAQ)</h2>"
            "<p>Tylko akapit bez listy.</p>"
        )
        out = tag_vouchery_faq_section(html)
        out = transform_vouchery_faq_editor_list_to_accordion(out)
        self.assertNotIn("content-accordion", out)
        self.assertIn("Tylko akapit bez listy.", out)


class TagVoucheryOfferSectionTests(SimpleTestCase):
    def test_wraps_body_under_chcesz_heading(self) -> None:
        html = (
            "<h2>CHCESZ ZASKOCZYĆ DZIECI ?</h2>"
            "<p>ZAREZERWUJ TEATR</p>"
            '<div class="elementor-button-wrapper"><a class="elementor-button">ZAPYTAJ</a></div>'
        )
        out = tag_vouchery_offer_section(html)
        self.assertIn("vouchery-offer-section__title", out)
        self.assertIn('class="vouchery-offer-body"', out)
        self.assertIn("ZAREZERWUJ", out)
        self.assertIn("ZAPYTAJ", out)

    def test_stops_at_next_h2(self) -> None:
        html = (
            "<h2>CHCESZ ZASKOCZYĆ DZIECI ?</h2>"
            "<p>One</p>"
            "<h2>Next section</h2>"
            "<p>Two</p>"
        )
        out = tag_vouchery_offer_section(html)
        self.assertEqual(out.count("</h2>"), 2, "Both section headings must remain")
        self.assertIn("vouchery-offer-body", out)
        self.assertIn("Next section", out)


class RemoveProductsGridTests(SimpleTestCase):
    def test_removes_ul_with_vouchery_products_grid_class(self) -> None:
        html = (
            "<p>Intro</p>"
            '<ul class="vouchery-products-grid"><li><h3><a href="/p/">T</a></h3>'
            '<p>d</p><p><a href="?add-to-cart=1">a</a></p></li></ul>'
            "<p>End</p>"
        )
        out = remove_products_grid_from_html(html)
        self.assertNotIn("vouchery-products-grid", out)
        self.assertIn("Intro", out)
        self.assertIn("End", out)


class SplitAfterFirstVoucheryPanelTests(SimpleTestCase):
    def test_two_sections_split(self) -> None:
        html = (
            '<section class="event-detail__panel event-content-block"><p>First</p></section>'
            '<section class="event-detail__panel event-content-block"><p>Second</p></section>'
        )
        first, rest = split_after_first_vouchery_panel(html)
        self.assertIn("First", first)
        self.assertIn("Second", rest)
        self.assertNotIn("Second", first)

    def test_single_section_returns_full_and_empty_rest(self) -> None:
        html = '<section class="event-detail__panel event-content-block"><p>Only</p></section>'
        first, rest = split_after_first_vouchery_panel(html)
        self.assertIn("Only", first)
        self.assertEqual(rest, "")


class SplitVoucheryPanelsTests(SimpleTestCase):
    def test_splits_pl_section_h2_into_multiple_sections(self) -> None:
        html = (
            "<h2>Intro</h2>"
            "<p>One</p>"
            "<h2>Jak wykorzystać voucher?</h2>"
            "<p>Two</p>"
            "<h2>Dlaczego voucher jest dobrym pomysłem na prezent?</h2>"
            "<p>Three</p>"
        )
        out = split_vouchery_content_into_panels(html, vouchery_button_href="/cart/", vouchery_button_label="L")
        self.assertEqual(out.count('<section class="event-detail__panel event-content-block">'), 3)
        self.assertIn("data-vouchery-button-href", out)
        self.assertIn("Intro", out)
        self.assertIn("Jak wykorzystać", out)

    def test_splits_en_section_h2_why_is_a_voucher(self) -> None:
        html = (
            "<h2>Give your loved ones unforgettable emotions</h2>"
            "<p>One</p>"
            "<h2>HOW TO USE A VOUCHER?</h2>"
            "<p>Two</p>"
            "<h2>WHY IS A VOUCHER A GREAT GIFT IDEA?</h2>"
            "<p>Three</p>"
        )
        out = split_vouchery_content_into_panels(html)
        self.assertEqual(out.count('<section class="event-detail__panel event-content-block">'), 3)
        self.assertIn("HOW TO USE", out)
        self.assertIn("WHY IS A VOUCHER", out)

    def test_single_panel_when_no_section_markers(self) -> None:
        html = "<h2>Only</h2><p>x</p>"
        out = split_vouchery_content_into_panels(html)
        self.assertEqual(out.count("<section"), 1)

    def test_splits_anonymous_shortcode_wrapper_divs_into_panels(self) -> None:
        """Former elementor-shortcode wrappers become classless divs; h2 must still split panels."""
        html = (
            "<h2>5 POWODÓW DLA KTÓRYCH</h2>"
            "<ul><li>x</li></ul>"
            '<a href="#">y</a>'
            "<div>"
            "<h2>CHCESZ ZASKOCZYĆ DZIECI ?</h2>"
            "<p>body</p>"
            "</div>"
            "<div>"
            "<h2>NAJCZĘŚCIEJ ZADAWANE PYTANIA (FAQ)</h2>"
            "<p>faq</p>"
            "</div>"
        )
        html = tag_vouchery_reasons_list(html)
        html = tag_vouchery_offer_section(html)
        html = tag_vouchery_faq_section(html)
        out = split_vouchery_content_into_panels(html)
        self.assertEqual(out.count('<section class="event-detail__panel event-content-block">'), 3)
        self.assertIn("vouchery-offer-section__title", out)
        self.assertIn("vouchery-faq-section__title", out)


class StripQuickViewTests(SimpleTestCase):
    def test_removes_premium_woo_quick_view_block(self) -> None:
        raw = (
            '<div><div class="premium-woo-qv-btn premium-woo-qv-btn-translate" '
            'data-product-id="1">Quick View<i class="premium-woo-qv-icon"></i></div>'
            "<p>Keep</p></div>"
        )
        out = strip_quick_view_from_html(raw)
        self.assertNotIn("Quick View", out)
        self.assertNotIn("premium-woo-qv", out)
        self.assertIn("Keep", out)


class TransformHtmlVoucheryIconsTests(SimpleTestCase):
    def test_angle_double_down_svg_becomes_css_hook_span(self) -> None:
        raw = """
        <div><a href="#voucher">
        <svg aria-hidden="true" class="e-font-icon-svg e-fas-angle-double-down"
             viewBox="0 0 320 512" xmlns="http://www.w3.org/2000/svg"><path d="M0 0"/></svg>
        </a></div>
        """
        out = transform_html(raw)
        self.assertNotIn("e-font-icon-svg", out)
        self.assertNotIn("<svg", out)
        self.assertIn("content-decor--chevrons-down", out)
        self.assertIn('aria-hidden="true"', out)

    def test_quick_view_strips_fa_eye_and_adds_class(self) -> None:
        raw = """
        <div class="premium-woo-qv-btn" data-product-id="1">Quick View
        <i class="premium-woo-qv-icon fa fa-eye"></i></div>
        """
        out = transform_html(raw)
        self.assertNotIn("fa-eye", out)
        self.assertNotIn("<i", out)
        self.assertIn("vouchery-quick-view", out)
        self.assertIn("Quick View", out)

    def test_modal_close_drops_fa_classes(self) -> None:
        raw = """<a class="premium-woo-quick-view-close fa fa-window-close" href="#"></a>"""
        out = transform_html(raw)
        self.assertNotIn("fa-window-close", out)
        self.assertIn("vouchery-modal-close", out)
        self.assertIn('aria-label="Zamknij"', out)

    def test_content_box_svg_loses_elementor_classes(self) -> None:
        raw = """
        <div class="content-box">
          <div class="content-box__icon"><span>
            <svg aria-hidden="true" class="e-font-icon-svg e-fas-list-ol"
                 xmlns="http://www.w3.org/2000/svg"><path d="M1"/></svg>
          </span></div>
          <p class="content-box__desc">Text</p>
        </div>
        """
        out = transform_html(raw)
        self.assertNotIn("e-font-icon-svg", out)
        self.assertIn("content-box__svg", out)
        self.assertIn("<svg", out)

    def test_cart_link_gets_data_marker(self) -> None:
        raw = """<a href="/cart/"><i class="fas fa-shopping-cart"></i></a>"""
        out = transform_html(raw)
        self.assertIn("data-vouchery-cart-widget", out)
        self.assertIn("vouchery-cart-widget", out)
        self.assertNotIn("<i", out)

    def test_elementor_accordion_becomes_details_with_answer(self) -> None:
        raw = """
        <div class="elementor-accordion">
          <div class="elementor-accordion-item">
            <div class="elementor-tab-title">
              <a class="elementor-accordion-title">Jak wygląda dostawa?</a>
            </div>
            <div class="elementor-tab-content"><p>PDF na email.</p></div>
          </div>
        </div>
        """
        out = transform_html(raw)
        self.assertIn("<details", out)
        self.assertIn('class="content-accordion__item"', out)
        self.assertIn("<summary", out)
        self.assertIn("content-accordion__title", out)
        self.assertIn("Jak wygląda dostawa?", out)
        self.assertIn("PDF na email.", out)
        self.assertNotIn("elementor-accordion", out)


# ---------------------------------------------------------------------------
# Themed pages utils
# ---------------------------------------------------------------------------

class StripElementorResidueTests(SimpleTestCase):
    def test_removes_premium_title_container(self) -> None:
        html = (
            '<div class="premium-title-container style9">'
            '<h2 class="premium-title-header">R<span class="premium-title-style9-letter">R</span></h2>'
            "</div>"
            "<p>Keep me</p>"
        )
        out = strip_elementor_residue(html)
        self.assertNotIn("premium-title-container", out)
        self.assertNotIn("premium-title-style9-letter", out)
        self.assertIn("Keep me", out)

    def test_unwraps_role_button_anchor_without_href(self) -> None:
        html = '<a role="button"><span><span>REPERTUAR</span></span></a>'
        out = strip_elementor_residue(html)
        self.assertNotIn('<a role="button">', out)
        self.assertIn("REPERTUAR", out)

    def test_keeps_anchor_with_href_hash(self) -> None:
        html = '<a href="#">ZAREZERWUJ BILETY</a>'
        out = strip_elementor_residue(html)
        self.assertIn('<a href="#">', out)
        self.assertIn("ZAREZERWUJ BILETY", out)

    def test_removes_empty_divs(self) -> None:
        html = "<h2>Title</h2><div></div><p>Body</p>"
        out = strip_elementor_residue(html)
        self.assertNotIn("<div></div>", out)
        self.assertIn("Title", out)
        self.assertIn("Body", out)


class ExtractMediaFromHtmlTests(SimpleTestCase):
    def test_extracts_img(self) -> None:
        html = '<p><img src="https://example.com/img.jpg" alt="Test photo"></p><p>Body</p>'
        images, videos, cleaned = extract_media_from_html(html)
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0]["src"], "https://example.com/img.jpg")
        self.assertEqual(images[0]["alt"], "Test photo")
        self.assertNotIn("<img", cleaned)
        self.assertIn("Body", cleaned)

    def test_extracts_video_src(self) -> None:
        html = (
            '<div class="e-hosted-video">'
            '<video controls src="https://example.com/vid.mp4"></video>'
            "</div>"
            "<p>Body</p>"
        )
        images, videos, cleaned = extract_media_from_html(html)
        self.assertEqual(len(videos), 1)
        self.assertEqual(videos[0]["video_url"], "https://example.com/vid.mp4")
        self.assertNotIn("<video", cleaned)
        self.assertIn("Body", cleaned)

    def test_extracts_iframe_embed(self) -> None:
        html = (
            '<div><iframe src="https://youtube.com/embed/abc123"></iframe></div>'
            "<p>Body</p>"
        )
        images, videos, cleaned = extract_media_from_html(html)
        self.assertEqual(len(videos), 1)
        self.assertIn("embed_url", videos[0])
        self.assertEqual(videos[0]["embed_url"], "https://youtube.com/embed/abc123")
        self.assertNotIn("<iframe", cleaned)

    def test_ignores_biletyna_iframe(self) -> None:
        html = '<div><iframe src="https://biletyna.pl/widget?id=1"></iframe></div><p>Body</p>'
        images, videos, cleaned = extract_media_from_html(html)
        self.assertEqual(len(videos), 0)


class SplitHtmlByH2IntoPanelsTests(SimpleTestCase):
    def test_content_before_first_h2_becomes_hero_intro(self) -> None:
        html = "<p>Subtitle</p><a href='#'>CTA</a><h2>Section One</h2><p>Body one</p>"
        out = split_html_by_h2_into_panels(html)
        self.assertIn("page-themed__hero-intro", out)
        self.assertIn("Subtitle", out)
        self.assertIn("CTA", out)

    def test_each_h2_starts_a_new_panel(self) -> None:
        html = (
            "<h2>First</h2><p>A</p>"
            "<h2>Second</h2><p>B</p>"
            "<h2>Third</h2><p>C</p>"
        )
        out = split_html_by_h2_into_panels(html)
        # First h2 → hero-intro; remaining 2 → event-content-block panels.
        self.assertEqual(out.count("event-content-block__body"), 2)
        self.assertIn("page-themed__hero-intro-body", out)
        self.assertIn("First", out)
        self.assertIn("B", out)
        self.assertIn("Third", out)

    def test_empty_html_returns_empty(self) -> None:
        self.assertEqual(split_html_by_h2_into_panels(""), "")

    def test_no_h2_entire_content_in_hero_intro(self) -> None:
        html = "<p>Only paragraph</p>"
        out = split_html_by_h2_into_panels(html)
        self.assertIn("page-themed__hero-intro", out)
        self.assertIn("Only paragraph", out)
        self.assertNotIn("event-content-block", out)

    def test_empty_chunk_before_first_h2_emits_no_hero_panel(self) -> None:
        """Gallery-only intro in DB becomes empty after extract_media; avoid blank section."""
        html = "<p></p><h2>Real section</h2><p>Body</p>"
        out = split_html_by_h2_into_panels(html)
        self.assertNotIn("page-themed__hero-intro", out)
        self.assertIn("event-content-block", out)
        self.assertIn("Real section", out)
        self.assertIn("Body", out)

    def test_whitespace_only_before_h2_emits_no_hero_panel(self) -> None:
        html = "<p>   </p><h2>Next</h2><p>Text</p>"
        out = split_html_by_h2_into_panels(html)
        self.assertNotIn("page-themed__hero-intro", out)
        self.assertIn("Next", out)


# ---------------------------------------------------------------------------
# Smoke tests for themed page views
# ---------------------------------------------------------------------------

class ThemedPageSmokeTests(TestCase):
    fixtures: list = []

    def setUp(self) -> None:
        from apps.pages.models import StaticPage
        for slug, title in [
            ("dla-dzieci", "Dla dzieci"),
            ("dla-szkol", "Dla szkół"),
            ("dla-firm", "Dla firm"),
            ("vouchery", "Vouchery"),
        ]:
            StaticPage.objects.get_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "content": f"<h2>{title}</h2><p>Test content for {slug}.</p>",
                    "is_published": True,
                    "layout_version": "v2" if slug == "vouchery" else "v1",
                },
            )

    def test_dla_dzieci_returns_200_with_theme_class(self) -> None:
        resp = self.client.get("/dla-dzieci/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "page-theme--dla-dzieci")

    def test_dla_szkol_returns_200_with_theme_class(self) -> None:
        resp = self.client.get("/dla-szkol/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "page-theme--dla-szkol")

    def test_dla_firm_returns_200_with_theme_class(self) -> None:
        resp = self.client.get("/dla-firm/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "page-theme--dla-firm")
        self.assertContains(resp, "group-inquiry-dialog")
        self.assertContains(resp, "dla-firm-group-dialog.js")

    def test_themed_pages_have_no_premium_title_residue(self) -> None:
        for slug in ("dla-dzieci", "dla-szkol", "dla-firm"):
            page = __import__("apps.pages.models", fromlist=["StaticPage"]).StaticPage.objects.get(slug=slug)
            page.content = (
                '<div class="premium-title-container style9">'
                '<h2>R<span class="premium-title-style9-letter">R</span></h2></div>'
                "<h2>Section</h2><p>Body</p>"
            )
            page.save()
            resp = self.client.get(f"/{slug}/")
            self.assertEqual(resp.status_code, 200)
            self.assertNotContains(resp, "premium-title-style9-letter")

    def test_vouchery_still_uses_v2_template(self) -> None:
        resp = self.client.get("/vouchery/")
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "page-theme--")
        # v2 template renders vouchery-page class
        self.assertContains(resp, "vouchery-page")


# ---------------------------------------------------------------------------
# Dla firm: CTA tagging + inquiry / contact POST
# ---------------------------------------------------------------------------


class TagDlaFirmGroupCtasTests(SimpleTestCase):
    def test_zarezerwuj_gets_rezerwacja(self) -> None:
        html = '<p><a href="#" class="btn">ZAREZERWUJ BILETY</a></p>'
        out = tag_dla_firm_group_ctas(html)
        self.assertIn('data-group-intent="rezerwacja"', out)

    def test_repertuar_without_zarezerwuj(self) -> None:
        html = '<p><a href="#">REPERTUAR</a></p>'
        out = tag_dla_firm_group_ctas(html)
        self.assertIn('data-group-intent="repertuar"', out)

    def test_preserves_manual_data_group_intent(self) -> None:
        html = '<a href="#" data-group-intent="other">CUSTOM</a>'
        out = tag_dla_firm_group_ctas(html)
        self.assertIn('data-group-intent="other"', out)

    def test_skips_external_href(self) -> None:
        html = '<a href="https://example.com/page">ZAREZERWUJ BILETY</a>'
        out = tag_dla_firm_group_ctas(html)
        self.assertNotIn("data-group-intent", out)


class WrapDlaFirmTicketsWordTests(SimpleTestCase):
    def test_wraps_last_word_bilety_after_repertuar(self) -> None:
        html = "<p>REPERTUAR ZAREZERWUJ BILETY</p>"
        out = wrap_dla_firm_tickets_word(html)
        self.assertIn("dla-firm-tickets-btn", out)
        self.assertIn('data-group-intent="rezerwacja"', out)

    def test_wraps_ru_line(self) -> None:
        html = "<p>РЕПЕРТУАР ЗАБРОНИРОВАТЬ БИЛЕТЫ</p>"
        out = wrap_dla_firm_tickets_word(html)
        self.assertIn("dla-firm-tickets-btn", out)

    def test_skips_when_group_intent_anchor_present(self) -> None:
        html = '<p>REPERTUAR <a href="#" data-group-intent="rezerwacja">BILETY</a></p>'
        out = wrap_dla_firm_tickets_word(html)
        self.assertNotIn("dla-firm-tickets-btn", out)
        self.assertIn("BILETY", out)


class MergeDlaFirmPanelPairsTests(SimpleTestCase):
    def test_merges_four_sections_into_two(self) -> None:
        panels = """
<section class="event-detail__panel page-themed__hero-intro">
<div class="page-themed__hero-intro-body"><h1>H</h1></div>
</section>
<section class="event-detail__panel event-content-block">
<div class="event-content-block__body"><h2>A</h2></div>
</section>
<section class="event-detail__panel event-content-block">
<div class="event-content-block__body"><h2>B</h2></div>
</section>
<section class="event-detail__panel event-content-block">
<div class="event-content-block__body"><h2>C</h2></div>
</section>
""".strip()
        out = merge_dla_firm_panel_pairs(panels)
        self.assertEqual(out.count("<section"), 2)
        self.assertIn("dla-firm__panel--merge-1", out)
        self.assertIn("dla-firm__panel--merge-2", out)

    def test_noop_with_two_sections(self) -> None:
        panels = """
<section class="event-detail__panel page-themed__hero-intro">
<div class="page-themed__hero-intro-body"><p>x</p></div>
</section>
<section class="event-detail__panel event-content-block">
<div class="event-content-block__body"><h2>A</h2></div>
</section>
""".strip()
        out = merge_dla_firm_panel_pairs(panels)
        self.assertEqual(out.count("<section"), 1)
        self.assertIn("dla-firm__panel--merge-1", out)


class GroupInquiryAndContactViewTests(TestCase):
    @override_settings(
        INQUIRY_EMAIL_TO=["ops@example.com"],
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_group_inquiry_post_sends_mail(self) -> None:
        mail.outbox.clear()
        self.assertEqual(GroupInquiry.objects.count(), 0)
        resp = self.client.post(
            "/group-inquiry/",
            {
                "name": "Jan Kowalski",
                "email": "jan@example.com",
                "phone": "",
                "company": "",
                "nip": "",
                "ticket_count": "",
                "message": "Proszę o kontakt.",
                "intent": "repertuar",
                "source_page": "dla-firm",
                "next": "/dla-firm/",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], "/dla-firm/")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("repertuar", mail.outbox[0].body.lower())
        self.assertEqual(GroupInquiry.objects.count(), 1)
        row = GroupInquiry.objects.get()
        self.assertEqual(row.email, "jan@example.com")
        self.assertEqual(row.intent, "repertuar")

    @override_settings(
        INQUIRY_EMAIL_TO=["ops@example.com"],
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_group_inquiry_invalid_sends_no_mail(self) -> None:
        mail.outbox.clear()
        self.assertEqual(GroupInquiry.objects.count(), 0)
        self.client.post(
            "/group-inquiry/",
            {
                "name": "",
                "email": "not-an-email",
                "message": "",
                "intent": "repertuar",
                "next": "/dla-firm/",
            },
        )
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(GroupInquiry.objects.count(), 0)

    @override_settings(
        INQUIRY_EMAIL_TO=["ops@example.com"],
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_contact_post_sends_mail(self) -> None:
        mail.outbox.clear()
        resp = self.client.post(
            "/contact/",
            {
                "name": "Anna",
                "email": "anna@example.com",
                "organization": "ACME",
                "message": "Hello",
                "next": "/polityka-prywatnosci/",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], "/polityka-prywatnosci/")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("kontakt", mail.outbox[0].subject.lower())

    @override_settings(INQUIRY_EMAIL_TO=[])
    def test_group_inquiry_empty_recipients_saves_db_no_mail(self) -> None:
        mail.outbox.clear()
        self.assertEqual(GroupInquiry.objects.count(), 0)
        resp = self.client.post(
            "/group-inquiry/",
            {
                "name": "Jan Kowalski",
                "email": "jan@example.com",
                "message": "x",
                "intent": "repertuar",
                "next": "/dla-firm/",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(GroupInquiry.objects.count(), 1)
