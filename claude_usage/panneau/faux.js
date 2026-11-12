// Faux pont pour le navigateur : garde l'état en mémoire et répond comme Python. Ne lance rien.
// ?etat= force un état pour les captures : vide, erreur, absent, limite, echue.
(function () {
  const sec = () => Math.floor(Date.now() / 1000);
  const copie = o => JSON.parse(JSON.stringify(o));

  function depart() {
    const t = sec();
    return { etat: "ok", message: null, actualisation: false,
      session: { pourcentage: 49, remise_a_zero: t + 2 * 3600 + 14 * 60, echue: false },
      semaine: { pourcentage: 20, remise_a_zero: t + 4 * 86400, echue: false },
      releve_a: t - 180,
      reglages: { demarrage: true, auto: false } };
  }

  function force(nom) {
    const e = depart(), t = sec();
    if (nom === "vide") Object.assign(e, { etat: "vide", session: null, semaine: null, releve_a: null });
    else if (nom === "erreur") Object.assign(e, { etat: "erreur", message: "Claude Code ne répond pas." });
    else if (nom === "absent") Object.assign(e, { etat: "absent", session: null, semaine: null, releve_a: null });
    else if (nom === "limite") { e.session.pourcentage = 100; e.semaine.pourcentage = 82; }
    else if (nom === "echue") Object.assign(e.session, { pourcentage: 0, remise_a_zero: t - 600, echue: true });
    return e;
  }

  let etat = force(new URLSearchParams(location.search).get("etat"));
  const repondre = delai => setTimeout(() => window.recevoir(copie(etat)), delai);

  window.fauxBridge = function (message) {
    if (message.action === "actualiser") {
      etat.actualisation = true;
      repondre(0);
      setTimeout(() => {
        const base = etat.etat === "ok" || etat.etat === "erreur" && etat.session ? etat : depart();
        base.etat = "ok"; base.message = null; base.actualisation = false;
        base.session.pourcentage = Math.min(100, base.session.pourcentage + 3);
        base.releve_a = sec();
        etat = base;
        window.recevoir(copie(etat));
      }, 1200);
    } else if (message.action === "auto" || message.action === "demarrage") {
      if (typeof message.on === "boolean") etat.reglages[message.action] = message.on;
      repondre(150);
    } else if (message.action === "quitter") console.log("quitter");
    else if (message.action === "auteur") window.open("https://github.com/anthamo", "_blank");
    else if (message.action === "pret") repondre(150);
  };
})();
