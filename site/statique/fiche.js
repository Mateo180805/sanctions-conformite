// Petites aides sur une fiche : bouton « Tout déplier », grief ouvert quand on arrive
// par un lien (#grief-3), et section en cours signalée dans le sommaire.
(function () {
  "use strict";
  var griefs = Array.prototype.slice.call(document.querySelectorAll("details.grief"));
  var bouton = document.getElementById("tout-ouvrir");
  if (bouton && griefs.length > 1) {
    bouton.hidden = false;
    bouton.addEventListener("click", function () {
      var ouvrir = griefs.some(function (g) { return !g.open; });
      griefs.forEach(function (g) { g.open = ouvrir; });
      bouton.textContent = ouvrir ? "Tout replier" : "Tout déplier";
    });
  }

  function ouvrirDepuisAdresse() {
    var cible = location.hash && document.getElementById(location.hash.slice(1));
    if (cible && cible.tagName === "DETAILS") cible.open = true;
  }
  ouvrirDepuisAdresse();
  window.addEventListener("hashchange", ouvrirDepuisAdresse);

  if (!("IntersectionObserver" in window)) return;
  var liens = {};
  document.querySelectorAll(".sommaire a").forEach(function (a) { liens[a.hash.slice(1)] = a; });
  var obs = new IntersectionObserver(function (entrees) {
    entrees.forEach(function (en) {
      if (!en.isIntersecting) return;
      Object.keys(liens).forEach(function (k) { liens[k].classList.remove("ici"); });
      var a = liens[en.target.id];
      if (a) a.classList.add("ici");
    });
  }, { rootMargin: "0px 0px -70% 0px" });
  document.querySelectorAll(".fiche-corps section[id]").forEach(function (s) { obs.observe(s); });
})();
