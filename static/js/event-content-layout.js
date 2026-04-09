/**
 * Imported HTML (Elementor/WP) may leave empty columns with inline width,
 * which creates a wide left/right gutter next to video. Hide columns with
 * no meaningful content so media can use full .event-content width.
 */
(function () {
    function columnHasMeaningfulContent(column) {
        if (
            column.querySelector(
                "video, iframe, img, svg, canvas, object, embed, table, blockquote, pre, ul, ol"
            )
        ) {
            return true;
        }
        const text = column.textContent.replace(/\s+/g, " ").trim();
        return text.length > 1;
    }

    function normalizeElementorColumns(root) {
        root.querySelectorAll(".elementor-column").forEach((col) => {
            if (!columnHasMeaningfulContent(col)) {
                col.hidden = true;
            }
        });
    }

    document.querySelectorAll(".event-content").forEach(normalizeElementorColumns);
})();
