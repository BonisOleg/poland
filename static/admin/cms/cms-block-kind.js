/**
 * cms-block-kind.js
 *
 * Per-row visibility filter for the PageBlock generic stacked inline.
 *
 * Each block row in Django admin is rendered as <div class="inline-related">
 * inside an outer <fieldset class="module cms-block-inline">. The previous
 * implementation scoped to the outer fieldset, so the *first* row's "kind"
 * drove visibility for ALL rows. This version scopes everything to the
 * .inline-related element, so every row controls its own field set.
 *
 * Scope: Django admin only (uses django.jQuery).
 * Degrades gracefully — if anything throws, all fields remain visible.
 */
(function ($) {
  'use strict';

  var HEADING = ['.field-heading_pl', '.field-heading_uk', '.field-heading_level'];
  var BODY    = ['.field-body_pl', '.field-body_uk'];

  // Map: block kind → list of field-row selectors that must be visible.
  // Selectors are matched against `.form-row` divs that Django labels with
  // `field-<name>` for each field in the row tuple. PageBlockInline groups
  // related fields in tuples (e.g. ("image", "image_alt")), so a single
  // .field-image selector already covers the full row including image_alt.
  var KIND_SHOW = {
    text:      HEADING.concat(BODY),
    image:     HEADING.concat(BODY).concat(['.field-image']),
    gallery:   HEADING.concat(['.field-gallery_items_count']),
    video:     HEADING.concat(BODY).concat(['.field-video_embed_url']),
    cta:       HEADING.concat(BODY).concat(['.field-button_text']),
    form:      HEADING.concat(['.field-form_kind']),
    countdown: HEADING.concat(['.field-countdown_target']),
    reviews:   HEADING.concat(['.field-reviews_limit']),
    related:   HEADING.concat(['.field-related_strategy']),
    html:      HEADING.concat(BODY)
  };

  // Union of every selector that may be hidden — reset target on each pass.
  var ALL_OPTIONAL = HEADING.concat(BODY).concat([
    '.field-image',
    '.field-video_embed_url',
    '.field-button_text',
    '.field-countdown_target',
    '.field-form_kind',
    '.field-reviews_limit',
    '.field-related_strategy',
    '.field-gallery_items_count'
  ]);

  function applyKindVisibility($row) {
    var kind = $row.find('select[name$="-kind"]').first().val();
    var toShow = KIND_SHOW[kind];

    if (!kind || !toShow) {
      $row.find(ALL_OPTIONAL.join(',')).show();
      return;
    }

    $row.find(ALL_OPTIONAL.join(',')).hide();
    $row.find(toShow.join(',')).show();
  }

  function initRow(rowEl) {
    var $row = $(rowEl);
    if ($row.hasClass('empty-form')) {
      return;
    }
    applyKindVisibility($row);
    $row.find('select[name$="-kind"]').on('change.cmsBlockKind', function () {
      applyKindVisibility($row);
    });
  }

  $(document).ready(function () {
    $('fieldset.cms-block-inline .inline-related').each(function () {
      initRow(this);
    });

    // Django fires formset:added with ($row, formsetName) on dynamic rows.
    $(document).on('formset:added', function (event, $row) {
      if (!$row || !$row.length) {
        return;
      }
      if ($row.hasClass('cms-block-inline') || $row.find('fieldset.cms-block-inline').length) {
        $row.find('.inline-related').each(function () {
          initRow(this);
        });
        return;
      }
      if ($row.hasClass('inline-related') && $row.closest('fieldset.cms-block-inline').length) {
        initRow($row.get(0));
      }
    });
  });

}(django.jQuery));
