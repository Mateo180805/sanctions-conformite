// Recherche, filtres et tri de la page « Base ».
// Sans JavaScript, le tableau complet reste lisible : ce script ne fait qu'ajouter les filtres.
(function () {
  "use strict";
  var form = document.getElementById("filtres");
  var corps = document.querySelector("#base tbody");
  if (!form || !corps) return;
  var lignes = Array.prototype.slice.call(corps.rows);
  var compte = document.getElementById("compte");
  var aucun = document.getElementById("aucun");
  var champs = {
    q: document.getElementById("f-recherche"),
    regulateur: document.getElementById("f-regulateur"),
    annee: document.getElementById("f-annee"),
    type: document.getElementById("f-groupe"),
    categorie: document.getElementById("f-categorie"),
    montant: document.getElementById("f-tranche"),
    theme: document.getElementById("f-theme"),
    fiche: document.getElementById("f-fiche")
  };
  form.hidden = false;

  // Sur téléphone, les filtres sont repliés derrière « Filtres » ; sur grand écran, toujours ouverts.
  var plus = document.getElementById("plus-filtres");
  var nbFiltres = document.getElementById("nb-filtres");
  var large = window.matchMedia("(min-width: 761px)");
  plus.open = large.matches;
  large.addEventListener("change", function () { if (large.matches) plus.open = true; });

  // Même règle que dans construire.py : minuscules et sans accents.
  function simplifier(t) {
    return t.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  }

  function filtrer() {
    var mots = simplifier(champs.q.value.trim()).split(/\s+/).filter(Boolean);
    var v = {
      regulateur: champs.regulateur.value, annee: champs.annee.value, type: champs.type.value,
      categorie: champs.categorie.value, montant: champs.montant.value, theme: champs.theme.value,
      fiche: champs.fiche.checked
    };
    var actifs = ["regulateur", "annee", "type", "categorie", "montant", "theme", "fiche"]
      .filter(function (k) { return v[k]; }).length;
    nbFiltres.textContent = actifs ? "(" + actifs + (actifs > 1 ? " actifs)" : " actif)") : "";
    var n = 0;
    lignes.forEach(function (tr) {
      var d = tr.dataset;
      var ok = (!v.regulateur || d.regulateur === v.regulateur) &&
        (!v.annee || d.annee === v.annee) &&
        (!v.type || d.groupe === v.type) &&
        (!v.categorie || d.categories.split("|").indexOf(v.categorie) !== -1) &&
        (!v.montant || d.tranche === v.montant) &&
        (!v.theme || d.lcbft === v.theme) &&
        (!v.fiche || d.fiche === "1") &&
        mots.every(function (m) { return d.recherche.indexOf(m) !== -1; });
      tr.hidden = !ok;
      if (ok) n++;
    });
    compte.textContent = n === 0 ? "Aucune décision" : n === 1 ? "1 décision" : n + " décisions";
    aucun.hidden = n !== 0;
    memoriser();
  }

  // Les filtres sont recopiés dans l'adresse de la page : on peut partager un lien filtré.
  function memoriser() {
    var p = new URLSearchParams();
    Object.keys(champs).forEach(function (k) {
      var c = champs[k];
      var val = c.type === "checkbox" ? (c.checked ? "1" : "") : c.value.trim();
      if (val) p.set(k, val);
    });
    var s = p.toString();
    history.replaceState(null, "", s ? "?" + s : location.pathname);
  }

  function lireAdresse() {
    var p = new URLSearchParams(location.search);
    Object.keys(champs).forEach(function (k) {
      if (!p.has(k)) return;
      var c = champs[k];
      if (c.type === "checkbox") c.checked = p.get(k) === "1";
      else c.value = p.get(k);
    });
  }

  // Fondu rapide du tableau quand on change un filtre ou un tri (navigateurs récents seulement).
  var calme = window.matchMedia("(prefers-reduced-motion: reduce)");
  function avecTransition(action) {
    if (document.startViewTransition && !calme.matches) document.startViewTransition(action);
    else action();
  }

  function effacer() {
    avecTransition(function () { form.reset(); filtrer(); });
    champs.q.focus();
  }

  // Tri par date ou par montant, en cliquant sur l'en-tête de colonne.
  function trier(bouton) {
    var th = bouton.parentNode;
    var cle = bouton.dataset.tri;
    var sens = th.getAttribute("aria-sort") === "descending" ? "ascending" : "descending";
    document.querySelectorAll(".base th[aria-sort]").forEach(function (x) { x.removeAttribute("aria-sort"); });
    th.setAttribute("aria-sort", sens);
    var signe = sens === "descending" ? -1 : 1;
    lignes.sort(function (a, b) {
      var x = a.dataset[cle], y = b.dataset[cle];
      if (cle === "montant") { x = +x; y = +y; }
      if (x === y) return (a.dataset.date < b.dataset.date ? 1 : -1);
      return (x < y ? -1 : 1) * signe;
    });
    lignes.forEach(function (tr) { corps.appendChild(tr); });
  }

  lireAdresse();
  // La recherche filtre à chaque lettre, sans animation ; les autres filtres avec un fondu.
  form.addEventListener("input", function (ev) { if (ev.target === champs.q) filtrer(); });
  form.addEventListener("change", function (ev) { if (ev.target !== champs.q) avecTransition(filtrer); });
  form.addEventListener("submit", function (ev) { ev.preventDefault(); });
  document.getElementById("f-effacer").addEventListener("click", effacer);
  document.querySelector("[data-effacer]").addEventListener("click", effacer);
  document.querySelectorAll(".base th button").forEach(function (b) {
    b.addEventListener("click", function () { avecTransition(function () { trier(b); }); });
  });
  filtrer();
})();
