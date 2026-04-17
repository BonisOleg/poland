(() => {
    'use strict';

    // ── Lightbox ──────────────────────────────────────────────
    const lightbox = document.getElementById('event-lightbox');
    if (lightbox) {
        const img     = lightbox.querySelector('.event-lightbox__img');
        const closeBtn = lightbox.querySelector('.event-lightbox__close');

        const open  = (src, alt) => { img.src = src; img.alt = alt; lightbox.showModal(); };
        const close = ()         => { lightbox.close(); img.src = ''; img.alt = ''; };

        document.querySelectorAll('.event-gallery__thumb-btn').forEach(btn => {
            btn.addEventListener('click', () => open(btn.dataset.lightboxSrc ?? '', btn.dataset.lightboxAlt ?? ''));
        });
        closeBtn?.addEventListener('click', close);
        lightbox.addEventListener('click', e => { if (e.target === lightbox) close(); });
        lightbox.addEventListener('cancel', close);
    }

    // ── Generic carousel ─────────────────────────────────────
    const initCarousel = (carousel) => {
        const viewport = carousel.parentElement;              // .event-gallery__carousel-viewport
        const wrap     = viewport?.parentElement;             // .event-gallery__carousel-wrap
        const section  = wrap?.parentElement;                 // .event-gallery (section)
        if (!wrap || !section) return;

        const prevBtn       = wrap.querySelector('.event-gallery__arrow--prev');
        const nextBtn       = wrap.querySelector('.event-gallery__arrow--next');
        const dotsContainer = section.querySelector('.event-gallery__dots');

        // ── helpers ──────────────────────────────────────────
        const items = () => Array.from(carousel.children);

        const getPerPage = () => {
            const first = carousel.firstElementChild;
            if (!first) return 1;
            const gap = parseFloat(getComputedStyle(carousel).columnGap) || 0;
            return Math.max(1, Math.round((carousel.clientWidth + gap) / (first.offsetWidth + gap)));
        };

        const getCurrentPage = () => {
            const perPage = getPerPage();
            const first   = carousel.firstElementChild;
            if (!first) return 0;
            const gap     = parseFloat(getComputedStyle(carousel).columnGap) || 0;
            const step    = first.offsetWidth + gap;
            return Math.round(carousel.scrollLeft / (step * perPage));
        };

        // ── dots ─────────────────────────────────────────────
        const buildDots = () => {
            if (!dotsContainer) return;
            dotsContainer.innerHTML = '';
            const count   = items().length;
            const perPage = getPerPage();
            const pages   = Math.ceil(count / perPage);
            if (pages <= 1) return;

            for (let i = 0; i < pages; i++) {
                const dot = document.createElement('button');
                dot.className = 'event-gallery__dot';
                dot.setAttribute('aria-label', `Strona ${i + 1}`);
                dot.addEventListener('click', () => {
                    const first = carousel.firstElementChild;
                    if (!first) return;
                    const gap  = parseFloat(getComputedStyle(carousel).columnGap) || 0;
                    const step = first.offsetWidth + gap;
                    carousel.scrollTo({ left: i * perPage * step, behavior: 'smooth' });
                });
                dotsContainer.appendChild(dot);
            }
            updateDots();
        };

        const updateDots = () => {
            if (!dotsContainer) return;
            const current = getCurrentPage();
            dotsContainer.querySelectorAll('.event-gallery__dot').forEach((dot, i) => {
                dot.classList.toggle('event-gallery__dot--active', i === current);
            });
        };

        // ── arrows ───────────────────────────────────────────
        const updateArrows = () => {
            const atStart = carousel.scrollLeft <= 4;
            const atEnd   = carousel.scrollLeft + carousel.clientWidth >= carousel.scrollWidth - 4;
            if (prevBtn) prevBtn.disabled = atStart;
            if (nextBtn) nextBtn.disabled = atEnd;
        };

        prevBtn?.addEventListener('click', () => carousel.scrollBy({ left: -carousel.clientWidth, behavior: 'smooth' }));
        nextBtn?.addEventListener('click', () => carousel.scrollBy({ left:  carousel.clientWidth, behavior: 'smooth' }));

        carousel.addEventListener('scroll', () => { updateArrows(); updateDots(); }, { passive: true });

        // ── init & resize ─────────────────────────────────────
        const setup = () => { buildDots(); updateArrows(); };
        // Defer to let layout settle before measuring widths
        requestAnimationFrame(setup);
        new ResizeObserver(setup).observe(carousel);
    };

    document.querySelectorAll('[data-carousel]').forEach(initCarousel);

    // ── City select dropdown (dla-dzieci page) ────────────────
    const citySelect = document.querySelector('.dla-dzieci-cities-select');
    if (citySelect) {
        citySelect.addEventListener('change', (e) => {
            const url = e.target.value;
            if (url) {
                window.location.href = url;
            }
        });
    }
})();
