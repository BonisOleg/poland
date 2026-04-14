(() => {
    'use strict';

    // ── Lightbox ──────────────────────────────────────────────
    const lightbox = document.getElementById('event-lightbox');
    if (lightbox) {
        const img = lightbox.querySelector('.event-lightbox__img');
        const closeBtn = lightbox.querySelector('.event-lightbox__close');

        const openLightbox = (src, alt) => {
            img.src = src;
            img.alt = alt;
            lightbox.showModal();
        };
        const closeLightbox = () => {
            lightbox.close();
            img.src = '';
            img.alt = '';
        };

        document.querySelectorAll('.event-gallery__thumb-btn').forEach(btn => {
            btn.addEventListener('click', () => openLightbox(
                btn.dataset.lightboxSrc ?? '',
                btn.dataset.lightboxAlt ?? ''
            ));
        });

        closeBtn?.addEventListener('click', closeLightbox);
        lightbox.addEventListener('click', e => { if (e.target === lightbox) closeLightbox(); });
        lightbox.addEventListener('cancel', closeLightbox);
    }

    // ── Carousel arrows ───────────────────────────────────────
    const carousel = document.getElementById('event-photo-carousel');
    if (!carousel) return;

    const prevBtn = document.querySelector('.event-gallery__arrow--prev');
    const nextBtn = document.querySelector('.event-gallery__arrow--next');

    const updateArrows = () => {
        const atStart = carousel.scrollLeft <= 4;
        const atEnd = carousel.scrollLeft + carousel.clientWidth >= carousel.scrollWidth - 4;
        prevBtn?.toggleAttribute('data-hidden', atStart);
        nextBtn?.toggleAttribute('data-hidden', atEnd);
    };

    prevBtn?.addEventListener('click', () => {
        carousel.scrollBy({ left: -carousel.clientWidth * 0.85, behavior: 'smooth' });
    });
    nextBtn?.addEventListener('click', () => {
        carousel.scrollBy({ left: carousel.clientWidth * 0.85, behavior: 'smooth' });
    });

    carousel.addEventListener('scroll', updateArrows, { passive: true });

    // Hide arrows if carousel doesn't overflow
    const checkOverflow = () => {
        const overflows = carousel.scrollWidth > carousel.clientWidth + 4;
        prevBtn?.toggleAttribute('data-hidden', !overflows || carousel.scrollLeft <= 4);
        nextBtn?.toggleAttribute('data-hidden', !overflows);
    };

    checkOverflow();
    new ResizeObserver(checkOverflow).observe(carousel);
})();
