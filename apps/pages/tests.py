"""Tests for pages app."""

from django.test import SimpleTestCase

from apps.pages.management.commands.clean_elementor_content import transform_html
from apps.pages.utils import strip_quick_view_from_html


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
