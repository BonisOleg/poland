/**
 * Makes each voucher product tile fully clickable using the heading product URL.
 * Add-to-cart / other links stay interactive above the full-card hit area.
 */
function findProductHref(li) {
    const headingLink = li.querySelector(":scope > :is(h2, h3) a[href]");
    if (headingLink) {
        const href = headingLink.getAttribute("href");
        return href && href !== "#" ? href : "";
    }
    return "";
}

function enhanceProductCards(root) {
    const items = root.querySelectorAll("ul.vouchery-products-grid > li");
    items.forEach((li) => {
        if (li.querySelector(":scope > .vouchery-product-card__hitarea")) {
            return;
        }
        const href = findProductHref(li);
        if (!href) {
            return;
        }
        const hit = document.createElement("a");
        hit.className = "vouchery-product-card__hitarea";
        hit.href = href;
        hit.setAttribute("aria-hidden", "true");
        hit.tabIndex = -1;
        li.prepend(hit);
    });
}

function init() {
    const root = document.querySelector(".event-content--vouchery");
    if (!root) {
        return;
    }
    enhanceProductCards(root);
}

init();
