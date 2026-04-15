"""Tests for pages app."""

from django.test import SimpleTestCase

from apps.pages.management.commands.clean_elementor_content import transform_html
from apps.pages.utils import (
    split_vouchery_content_into_panels,
    strip_quick_view_from_html,
    tag_vouchery_faq_section,
    tag_vouchery_offer_section,
    tag_vouchery_reasons_list,
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
        self.assertEqual(out.count("<h2>"), 2)
        self.assertIn("vouchery-offer-body", out)
        self.assertIn("Next section", out)


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
