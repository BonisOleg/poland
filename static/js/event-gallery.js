(() => {
    'use strict';

    const lightbox = document.getElementById('event-lightbox');
    if (!lightbox) return;

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
        btn.addEventListener('click', () => {
            openLightbox(
                btn.dataset.lightboxSrc ?? '',
                btn.dataset.lightboxAlt ?? ''
            );
        });
    });

    closeBtn?.addEventListener('click', closeLightbox);

    lightbox.addEventListener('click', e => {
        if (e.target === lightbox) closeLightbox();
    });

    lightbox.addEventListener('cancel', closeLightbox);
})();
