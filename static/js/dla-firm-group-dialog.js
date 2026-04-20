/**
 * Opens the group inquiry dialog when a CTA with data-group-intent is clicked.
 * Scoped to .page-theme--dla-firm only.
 */
(function () {
    const root = document.querySelector('.page-theme--dla-firm');
    if (!root) {
        return;
    }

    const dialog = document.getElementById('group-inquiry-dialog');
    const intentSelect = document.getElementById('group-inquiry-intent');
    if (!dialog || !intentSelect) {
        return;
    }

    const closeBtn = dialog.querySelector('.group-inquiry-dialog__close');

    function setIntent(value) {
        if (!value) {
            return;
        }
        for (let i = 0; i < intentSelect.options.length; i += 1) {
            if (intentSelect.options[i].value === value) {
                intentSelect.selectedIndex = i;
                return;
            }
        }
    }

    function openModal(intent) {
        setIntent(intent);
        dialog.showModal();
    }

    function closeModal() {
        dialog.close();
    }

    root.addEventListener('click', function (e) {
        const a = e.target.closest('a[data-group-intent]');
        if (!a || !root.contains(a)) {
            return;
        }
        e.preventDefault();
        openModal(a.getAttribute('data-group-intent'));
    });

    if (closeBtn) {
        closeBtn.addEventListener('click', closeModal);
    }

    dialog.addEventListener('click', function (e) {
        if (e.target === dialog) {
            closeModal();
        }
    });

    dialog.addEventListener('cancel', closeModal);
})();
