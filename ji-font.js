/* JI Engineering Style — registers the theme's typefaces. Nothing else.
 *
 * A Home Assistant theme is a list of CSS variables, and `@font-face` cannot be
 * one: a family has to be registered from the document, never from a card's
 * shadow root. So the faces ship as this module, wired through the frontend's
 * own hook for exactly this, `extra_module_url`:
 *
 *   frontend:
 *     themes: !include_dir_merge_named themes
 *     extra_module_url:
 *       - /local/ji/ji-font.js?v=1
 *
 * It loads on every frontend page, dialogs included, and styles nothing — where
 * the faces are used is the theme's decision (ha-font-family-*, mdc-*). Without
 * this module the stacks in the theme fall back to the system sans/mono and the
 * theme still works; it just stops using Manrope / JetBrains Mono.
 *
 * Manrope and JetBrains Mono both carry the full Polish glyph set. They are
 * loaded from Google Fonts (the browser fetches them, not the HA host). For a
 * fully offline panel, self-host the .woff2 and swap the href below.
 */
(() => {
  if (window.__jiFont) return;
  window.__jiFont = true;

  const links = [
    ['preconnect', 'https://fonts.googleapis.com'],
    ['preconnect', 'https://fonts.gstatic.com', true],
    ['stylesheet',
      'https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500&display=swap'],
  ];
  for (const [rel, href, crossorigin] of links) {
    const el = document.createElement('link');
    el.rel = rel;
    el.href = href;
    if (crossorigin) el.crossOrigin = 'anonymous';
    el.className = 'ji-font';
    document.head.appendChild(el);
  }
})();
