"use strict";

const pont = window.webkit?.messageHandlers?.pont;
const racine = document.getElementById("panneau");
let etat = null;

// Les textes viennent de Python : jamais dans le HTML sans passer par ici.
const ech = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function envoyer(message) {
  if (pont) pont.postMessage(message);
  else window.fauxBridge(message);
}

// Apparence : suit celle du Mac. En démonstration (navigateur), ?theme=sombre ou ?theme=clair la force.
const apparenceSombre = window.matchMedia("(prefers-color-scheme: dark)");
function poserTheme() {
  const force = new URLSearchParams(location.search).get("theme");
  const sombre = !pont && (force === "sombre" || force === "clair") ? force === "sombre" : apparenceSombre.matches;
  document.documentElement.dataset.theme = sombre ? "sombre" : "clair";
}
poserTheme();
apparenceSombre.addEventListener("change", poserTheme);

// ---- Le temps : la page met en forme les dates, Python ne donne que des secondes Unix ----

const DEUX = { hour: "2-digit", minute: "2-digit" };
const heure = d => d.toLocaleTimeString("fr-FR", DEUX);
const debutJour = d => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();

function age(secondes, maintenant) {
  const min = Math.floor((maintenant - secondes * 1000) / 60000);
  if (min < 1) return "Relevé à l'instant";
  if (min < 60) return `Relevé il y a ${min} min`;
  if (min < 1440) return `Relevé il y a ${Math.floor(min / 60)} h`;
  return `Relevé il y a ${Math.floor(min / 1440)} j`;
}

// « dans … » est donné le jour même, et pour le lendemain quand c'est dans moins de douze heures.
function dans(ms) {
  const min = Math.floor(ms / 60000);
  if (min < 1) return "dans moins d'une minute";
  if (min < 60) return `dans ${min} min`;
  return `dans ${Math.floor(min / 60)} h ${String(min % 60).padStart(2, "0")}`;
}

function remise(secondes, maintenant) {
  const d = new Date(secondes * 1000);
  const jours = Math.round((debutJour(d) - debutJour(new Date(maintenant))) / 86400000);
  if (jours <= 0) return `Remise à zéro à ${heure(d)} · ${dans(d.getTime() - maintenant)}`;
  // Passé minuit de peu : « demain à 01:00 » ne dit pas que c'est dans deux heures. On le précise sous douze heures.
  if (jours === 1) return `Remise à zéro demain à ${heure(d)}` + (d.getTime() - maintenant < 12 * 3600000 ? ` · ${dans(d.getTime() - maintenant)}` : "");
  if (jours <= 6) return `Remise à zéro ${d.toLocaleDateString("fr-FR", { weekday: "long" }).toLowerCase()} à ${heure(d)}`;
  return `Remise à zéro le ${d.toLocaleDateString("fr-FR", { day: "numeric", month: "long" })} à ${heure(d)}`;
}

// Une fenêtre dont l'heure est passée vaut échue même si aucun état n'est arrivé (ARCHITECTURE, décision 5).
const echue = (f, maintenant) => !!f && (f.echue || f.remise_a_zero * 1000 <= maintenant);

// ---- Le dessin ----

const ROUE = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M6.96 2.90L7.15 1.05L8.85 1.05L9.04 2.90L10.87 3.66L12.31 2.48L13.52 3.69L12.34 5.13L13.10 6.96L14.95 7.15L14.95 8.85L13.10 9.04L12.34 10.87L13.52 12.31L12.31 13.52L10.87 12.34L9.04 13.10L8.85 14.95L7.15 14.95L6.96 13.10L5.13 12.34L3.69 13.52L2.48 12.31L3.66 10.87L2.90 9.04L1.05 8.85L1.05 7.15L2.90 6.96L3.66 5.13L2.48 3.69L3.69 2.48L5.13 3.66Z" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/><circle cx="8" cy="8" r="2.2" fill="none" stroke="currentColor" stroke-width="1.2"/></svg>';

const carteFenetre = (cle, titre) =>
  `<section class="fenetre" data-f="${cle}"><div class="rang"><h2 class="titre">${titre}</h2><span class="pct"></span></div>
    <div class="barre" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-label="${titre}"><i></i></div><div class="info"></div></section>`;

function creerSquelette() {
  racine.innerHTML =
    `<div class="entete"><div class="noms"><div class="piece">Claude</div><div class="etat"></div></div><button type="button" class="roue" aria-label="Réglages" aria-pressed="false">${ROUE}</button></div>
    <div class="cartes">${carteFenetre("session", "Session actuelle")}${carteFenetre("semaine", "Cette semaine")}</div>
    <div class="reglages" hidden>
      <div class="bloc court"><div class="ligne"><span>Lancer à l'ouverture de session</span><button type="button" class="inter" role="switch" aria-checked="false" aria-label="Lancer à l'ouverture de session" data-reglage="demarrage"></button></div></div>
      <div class="bloc"><div class="ligne"><span>Actualiser toutes les 15 minutes</span><button type="button" class="inter" role="switch" aria-checked="false" aria-label="Actualiser toutes les 15 minutes" data-reglage="auto"></button></div>
        <div class="note">Chaque actualisation consomme un peu de l'abonnement.</div></div>
      <button type="button" class="quitter"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 2v6M4.6 4.2a5 5 0 1 0 6.8 0" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>Quitter Claude Usage</button>
      <div class="bas"><button type="button" class="auteur">Application créée par Anthony Hamo</button><button type="button" class="termine">Terminé</button></div>
    </div>`;
}

// « Actualisation… » dès le clic, avant la réponse de Python.
let enCours = false;

function ligneEtat(maintenant) {
  if (enCours || etat.actualisation) return "Actualisation…";
  const lien = t => `<button type="button" class="lien" data-actualiser>${t}</button>`;
  if (etat.etat === "absent") return "Claude Code n'est pas installé sur ce Mac.";
  if (etat.etat === "erreur") return `${ech(etat.message || "L'actualisation a échoué.")} · ${lien("Réessayer")}`;
  if (etat.etat === "vide" || typeof etat.releve_a !== "number") return `Aucun relevé · ${lien("Actualiser")}`;
  return `${age(etat.releve_a, maintenant)} · ${lien("Actualiser")}`;
}

function majFenetre(cle, f, maintenant) {
  const el = racine.querySelector(`[data-f="${cle}"]`);
  const pct = el.querySelector(".pct"), barre = el.querySelector(".barre"), plein = barre.querySelector("i"), info = el.querySelector(".info");
  let n = 0, niveau = "";
  if (!f) {
    pct.textContent = "–";
    info.textContent = "Pas encore de relevé";
    barre.removeAttribute("aria-valuenow");
  } else if (echue(f, maintenant)) {
    pct.textContent = "0 %";
    info.textContent = "Remise à zéro faite";
    barre.setAttribute("aria-valuenow", "0");
  } else {
    n = Math.max(0, Math.min(100, Math.round(f.pourcentage)));
    niveau = n >= 90 ? "limite" : n >= 75 ? "attention" : "";
    pct.textContent = `${n} %`;
    info.textContent = remise(f.remise_a_zero, maintenant);
    barre.setAttribute("aria-valuenow", String(n));
  }
  el.className = "fenetre" + (niveau ? " " + niveau : "");
  // Le premier dessin pose la largeur sans transition : la barre ne part pas de zéro à l'ouverture (et reste stable en capture).
  const premier = !plein.dataset.pose;
  if (premier) { plein.style.transition = "none"; plein.dataset.pose = "1"; }
  plein.style.width = n > 0 ? `max(8px, ${n}%)` : "0";
  if (premier) { plein.getBoundingClientRect(); plein.style.transition = ""; }
}

let reglagesOuverts = false, derniereHauteur = null;

function dessiner() {
  if (!racine.querySelector(".entete")) creerSquelette();
  if (etat) {
    const maintenant = Date.now();
    racine.querySelector(".entete .etat").innerHTML = ligneEtat(maintenant);
    majFenetre("session", etat.session, maintenant);
    majFenetre("semaine", etat.semaine, maintenant);
    racine.querySelectorAll("[data-reglage]").forEach(b => b.setAttribute("aria-checked", String(!!etat.reglages?.[b.dataset.reglage])));
  }
  signalerHauteur();
}

// L'app dimensionne la fenêtre sur cette valeur ; on ne l'envoie que si elle change.
function signalerHauteur() {
  if (!pont) return;
  const px = Math.round(racine.getBoundingClientRect().height);
  if (px === derniereHauteur) return;
  derniereHauteur = px;
  envoyer({ action: "hauteur", px });
}

function basculerReglages(ouvrir) {
  reglagesOuverts = ouvrir;
  racine.classList.toggle("en-reglages", ouvrir);
  racine.querySelector(".reglages").hidden = !ouvrir;
  racine.querySelector(".roue").setAttribute("aria-pressed", String(ouvrir));
  signalerHauteur();
}

// L'app donne la couleur d'accent choisie dans les réglages du Mac ; le navigateur garde le vert par défaut.
window.accent = couleur => racine.style.setProperty("--inter-on", couleur);

window.recevoir = function (nouvelEtat) {
  etat = nouvelEtat;
  enCours = false;
  dessiner();
};

// Le geste s'affiche tout de suite ; l'état reçu ensuite fait foi.
racine.addEventListener("click", e => {
  const b = e.target.closest("button");
  if (!b) return;
  if (b.classList.contains("roue")) { basculerReglages(!reglagesOuverts); return; }
  if ("actualiser" in b.dataset) {
    enCours = true;
    dessiner();
    envoyer({ action: "actualiser" });
  } else if (b.dataset.reglage) {
    const on = b.getAttribute("aria-checked") !== "true";
    b.setAttribute("aria-checked", String(on));
    if (etat) etat.reglages = { ...etat.reglages, [b.dataset.reglage]: on };
    envoyer({ action: b.dataset.reglage, on });
  } else if (b.classList.contains("quitter")) envoyer({ action: "quitter" });
  else if (b.classList.contains("termine")) basculerReglages(false);
  else if (b.classList.contains("auteur")) envoyer({ action: "auteur" });  // l'app ouvre la page GitHub dans le navigateur
});

// Le temps passe : âge du relevé, « dans … », fenêtre qui vient d'échoir.
setInterval(() => { if (etat) dessiner(); }, 30000);

function charger(src) {
  return new Promise((ok, ko) => {
    const s = document.createElement("script");
    s.src = src; s.onload = ok; s.onerror = ko;
    document.body.appendChild(s);
  });
}

async function demarrer() {
  creerSquelette();
  signalerHauteur();
  if (!pont) {
    document.documentElement.classList.add("demo");
    await charger("faux.js");
  }
  envoyer({ action: "pret" });
}
demarrer();
