/**
 * Imported HTML (Elementor/WP) may leave empty columns/containers with inline width,
 * which creates a wide left/right gutter next to video. Hide columns/containers with
 * no meaningful content so media can use full .event-content width.
 */
(function () {
    function hasMeaningfulContent(el) {
        if (
            el.querySelector(
                "video, iframe, img, svg, canvas, object, embed, table, blockquote, pre, ul, ol"
            )
        ) {
            return true;
        }
        const text = el.textContent.replace(/\s+/g, " ").trim();
        return text.length > 1;
    }

    function normalizeElementorColumns(root) {
        root.querySelectorAll(".elementor-column").forEach((col) => {
            if (!hasMeaningfulContent(col)) {
                col.hidden = true;
            }
        });
    }

    function normalizeElementorChildContainers(root) {
        root.querySelectorAll(".e-con.e-child").forEach((con) => {
            if (!hasMeaningfulContent(con)) {
                con.hidden = true;
            }
        });
    }

    document.querySelectorAll(".event-content").forEach((root) => {
        normalizeElementorColumns(root);
        normalizeElementorChildContainers(root);
    });
})();
