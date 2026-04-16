/**
 * Replaces the large Elementor cart icon on /vouchery/ with an outline button.
 * Preserves an existing link href from the imported markup when present.
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
    a.className = "btn btn--outline btn--lg btn--block vouchery-cart-btn";
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
 * First vouchery panel: wrap the hero line (e.g. «ZAPYTAJ O OFERTĘ») in a gradient CTA link.
 * Only runs when the first direct <p> has no link yet.
 */
function wrapHeroCtaLink(panelBody) {
    const href = panelBody.dataset.voucheryButtonHref || "#voucher";
    const firstP = panelBody.querySelector(":scope > p:first-of-type");
    if (!firstP || firstP.querySelector("a")) {
        return;
    }
    const a = document.createElement("a");
    a.href = href;
    a.className = "vouchery-hero-cta-link";
    while (firstP.firstChild) {
        a.appendChild(firstP.firstChild);
    }
    firstP.appendChild(a);
}

function init() {
    const heroPanel = document.querySelector(
        ".event-content-block__body.event-content--vouchery[data-vouchery-button-href]",
    );
    if (heroPanel) {
        wrapHeroCtaLink(heroPanel);
    }

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
