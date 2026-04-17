/**
 * Replaces the large Elementor cart icon on /vouchery/ with a primary gradient pill CTA.
 * Preserves an existing link href from the imported markup when present.
 *
 * Also supports new clean HTML with data-vouchery-cart-widget attribute.
 */
function findCartWidget(root) {
    const icons = [...root.querySelectorAll(".elementor-widget-icon")];
    if (icons.length) {
        return icons[icons.length - 1];
    }
    const iconBoxes = [...root.querySelectorAll(".elementor-widget-icon-box")];
    if (iconBoxes.length) {
        return iconBoxes[iconBoxes.length - 1];
    }
    const images = [...root.querySelectorAll(".elementor-widget-image")];
    if (images.length) {
        return images[images.length - 1];
    }
    const cartImg = [...root.querySelectorAll("img")].find((img) => {
        const src = (img.getAttribute("src") || "").toLowerCase();
        const alt = (img.getAttribute("alt") || "").toLowerCase();
        return /cart|koszyk|gift/.test(src) || /cart|koszyk|prezent/.test(alt);
    });
    if (cartImg) {
        return (
            cartImg.closest(".elementor-widget-image") ||
            cartImg.closest("figure") ||
            cartImg.closest("p") ||
            cartImg.parentElement
        );
    }
    return null;
}

function resolveHref(widget, fallback) {
    const link = widget.querySelector("a[href]");
    if (link) {
        return link.getAttribute("href") || fallback;
    }
    return fallback;
}

function replaceWithButton(widget, href, label) {
    const finalHref = resolveHref(widget, href);
    const a = document.createElement("a");
    a.href = finalHref;
    a.className = "btn btn--primary btn--lg btn--block vouchery-cart-btn";
    a.textContent = label;

    const container = widget.querySelector(".elementor-widget-container");
    if (container) {
        container.replaceChildren(a);
        return true;
    }
    widget.replaceWith(a);
    return true;
}

/**
 * «CHCESZ ZASKOCZYĆ…» / «ASK FOR AN OFFER» block only: short CTA line → gradient link (#voucher).
 * Do NOT touch the first intro panel — wrapping its first <p> broke EN (whole block became a button).
 */
function wrapOfferSectionCta() {
    const href = "#voucher";
    document.querySelectorAll(".vouchery-offer-body").forEach((body) => {
        const candidates = [...body.querySelectorAll(":scope > p")].filter((p) => !p.querySelector("a"));
        if (!candidates.length) {
            return;
        }
        const targetP = [...candidates].reverse().find((p) => {
            const t = (p.textContent || "").trim();
            if (t.length > 220) {
                return false;
            }
            const lower = t.toLowerCase();
            return /zapytaj o ofert|ask for an offer|ask for offer|request (an? )?offer|poproś o ofert|zamów ofert|inquire about (an? )?offer/i.test(
                lower,
            );
        });
        if (!targetP) {
            return;
        }
        const a = document.createElement("a");
        a.href = href;
        a.className = "vouchery-cta-gradient-link";
        while (targetP.firstChild) {
            a.appendChild(targetP.firstChild);
        }
        targetP.appendChild(a);
    });
}

function init() {
    wrapOfferSectionCta();

    const root = document.querySelector(".event-content--vouchery");
    if (!root) {
        return;
    }
    const fallbackHref = root.dataset.voucheryButtonHref || "#voucher";
    const label = root.dataset.voucheryButtonLabel || "KLIKNIJ PO PREZENT";

    const marked = root.querySelector("[data-vouchery-cart-widget], .vouchery-cart-widget");
    const widget = marked || findCartWidget(root);
    if (!widget) {
        return;
    }
    replaceWithButton(widget, fallbackHref, label);
}

init();
