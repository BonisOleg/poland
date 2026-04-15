/**
 * Elementor FAQ markup in .vouchery-faq-body (when clean_elementor_content was not applied).
 * Toggles .is-open on .elementor-accordion-item; CSS shows/hides .elementor-tab-content.
 */
function toggleItem(accordion, item, titleEl) {
    const willOpen = !item.classList.contains("is-open");
    accordion.querySelectorAll(".elementor-accordion-item.is-open").forEach((openItem) => {
        if (openItem !== item) {
            openItem.classList.remove("is-open");
            const t = openItem.querySelector(".elementor-tab-title");
            if (t) {
                t.setAttribute("aria-expanded", "false");
            }
        }
    });
    if (willOpen) {
        item.classList.add("is-open");
        titleEl.setAttribute("aria-expanded", "true");
    } else {
        item.classList.remove("is-open");
        titleEl.setAttribute("aria-expanded", "false");
    }
}

function initElementorFaq(accordion) {
    accordion.querySelectorAll(".elementor-tab-title").forEach((titleEl) => {
        if (titleEl.getAttribute("aria-expanded") == null) {
            titleEl.setAttribute("aria-expanded", "false");
        }
        if (!titleEl.hasAttribute("tabindex")) {
            titleEl.setAttribute("tabindex", "0");
        }
    });

    accordion.addEventListener("click", (e) => {
        const titleEl = e.target.closest(".elementor-tab-title");
        if (!titleEl || !accordion.contains(titleEl)) {
            return;
        }
        e.preventDefault();
        const item = titleEl.closest(".elementor-accordion-item");
        if (!item || !accordion.contains(item)) {
            return;
        }
        toggleItem(accordion, item, titleEl);
    });

    accordion.addEventListener("keydown", (e) => {
        if (e.key !== "Enter" && e.key !== " ") {
            return;
        }
        const titleEl = e.target.closest(".elementor-tab-title");
        if (!titleEl || !accordion.contains(titleEl)) {
            return;
        }
        e.preventDefault();
        const item = titleEl.closest(".elementor-accordion-item");
        if (!item || !accordion.contains(item)) {
            return;
        }
        toggleItem(accordion, item, titleEl);
    });
}

function init() {
    const faqBody = document.querySelector(".vouchery-faq-body");
    if (!faqBody) {
        return;
    }
    const accordion = faqBody.querySelector(".elementor-accordion");
    if (!accordion) {
        return;
    }
    initElementorFaq(accordion);
}

init();
