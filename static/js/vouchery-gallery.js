/**
 * Lightbox for .vouchery-gallery on /vouchery/ (v2 layout).
 * Opens full-size image on trigger click; closes on Escape, overlay click, or close button.
 */

const GALLERY_SEL = ".vouchery-gallery";
const TRIGGER_SEL = ".vouchery-gallery__trigger";
const LB_CLASS = "vouchery-lightbox";
const LB_IMG_CLASS = "vouchery-lightbox__img";
const LB_CLOSE_CLASS = "vouchery-lightbox__close";

let lightbox = null;

function openLightbox(src, alt) {
    if (lightbox) return;

    lightbox = document.createElement("div");
    lightbox.className = LB_CLASS;
    lightbox.setAttribute("role", "dialog");
    lightbox.setAttribute("aria-modal", "true");
    lightbox.setAttribute("aria-label", alt || "Podgląd zdjęcia");

    const img = document.createElement("img");
    img.src = src;
    img.alt = alt ?? "";
    img.className = LB_IMG_CLASS;

    const closeBtn = document.createElement("button");
    closeBtn.className = LB_CLOSE_CLASS;
    closeBtn.setAttribute("aria-label", "Zamknij");
    closeBtn.type = "button";
    closeBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        closeLightbox();
    });

    lightbox.append(img, closeBtn);
    lightbox.addEventListener("click", closeLightbox);
    img.addEventListener("click", (e) => e.stopPropagation());

    document.body.append(lightbox);
    document.addEventListener("keydown", onKeyDown);
}

function closeLightbox() {
    lightbox?.remove();
    lightbox = null;
    document.removeEventListener("keydown", onKeyDown);
}

function onKeyDown(e) {
    if (e.key === "Escape") closeLightbox();
}

function init() {
    const gallery = document.querySelector(GALLERY_SEL);
    if (!gallery) return;

    gallery.addEventListener("click", (e) => {
        const trigger = e.target.closest(TRIGGER_SEL);
        if (!trigger) return;
        const src = trigger.dataset.src;
        const alt = trigger.dataset.alt ?? "";
        if (src) openLightbox(src, alt);
    });
}

init();
