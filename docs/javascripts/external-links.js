/*
 * Open links that leave the site in a new tab.
 *
 * Material re-renders the page on navigation when `navigation.instant` is on, so this hooks
 * into the theme's `document$` observable rather than running once on load.
 */
document$.subscribe(function () {
  const here = window.location.hostname;
  document.querySelectorAll("article a[href^='http']").forEach(function (link) {
    if (link.hostname && link.hostname !== here) {
      link.target = "_blank";
      link.rel = "noopener noreferrer";
    }
  });
});
