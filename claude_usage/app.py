"""L'app : la jauge dans la barre de menus, le panneau en verre, la page.

Seul fichier qui importe AppKit / WebKit / PyObjCTools. Tout le reste (relevé, sonde, ligne d'état) se teste sans Mac.
Le socle (fenêtre en verre, marge, page transparente) vient de Hue Controller.
"""

import fcntl
import json
import sys
import threading
import time
from pathlib import Path

import objc
from AppKit import (
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSAttributedString,
    NSBackingStoreBuffered,
    NSColor,
    NSColorSpace,
    NSEvent,
    NSEventMaskLeftMouseDown,
    NSEventMaskRightMouseDown,
    NSFont,
    NSFontAttributeName,
    NSForegroundColorAttributeName,
    NSImage,
    NSMakeRect,
    NSObject,
    NSPanel,
    NSPopUpMenuWindowLevel,
    NSScreen,
    NSStatusBar,
    NSVariableStatusItemLength,
    NSView,
    NSVisualEffectView,
    NSWindowStyleMaskBorderless,
    NSWindowStyleMaskNonactivatingPanel,
    NSWorkspace,
)
from Foundation import NSJSONSerialization, NSURL
from PyObjCTools import AppHelper
from WebKit import WKWebView, WKWebViewConfiguration

from . import demarrage, reglages, releve, sonde

DOSSIER_PAGE = Path(__file__).parent / "panneau"
PAGE_AUTEUR = "https://github.com/anthamo"  # ouverte par la signature des réglages
LARGEUR = 360
HAUTEUR_DEPART = 280  # avant que la page n'ait dit sa vraie hauteur
HAUTEUR_MAXI = 640
MARGE = 32  # la fenêtre dépasse le panneau de cette marge, pour que l'ombre du verre ait la place de s'éteindre
RAYON = 20
ECART = 6  # entre la barre de menus et le panneau
VEILLE = 2  # secondes entre deux regards sur le fichier de relevé
AUTO = 15 * 60  # secondes entre deux actualisations automatiques, si l'utilisateur les a demandées
ESSAI = "--essai" in sys.argv

# L'icône de la barre de menus : blanc sur fond transparent, 88 px. Déclarée « modèle »,
# macOS la teint lui-même en noir ou en blanc selon la barre. Elle ne bouge pas : le niveau, c'est le pourcentage à côté.
ICONE_BARRE = Path(__file__).resolve().parent / "barre.png"
TAILLE_BARRE = 18  # points


def icone_barre():
    image = NSImage.alloc().initWithContentsOfFile_(str(ICONE_BARRE))
    if image is None:  # fichier absent : le symbole du système, plutôt qu'une barre de menus vide
        return NSImage.imageWithSystemSymbolName_accessibilityDescription_("gauge.medium", "Consommation de Claude")
    image.setSize_((TAILLE_BARRE, TAILLE_BARRE))
    image.setTemplate_(True)
    image.setAccessibilityDescription_("Consommation de Claude")
    return image


class Fenetre(NSPanel):
    def canBecomeKeyWindow(self):  # sans ça, une fenêtre sans bord refuse les clics dans la page
        return True


def fond_en_verre(page, hauteur):
    """Le verre des panneaux de macOS 26, sinon le flou des versions d'avant (jamais essayé)."""
    cadre = NSMakeRect(0, 0, LARGEUR, hauteur)
    try:
        verre = objc.lookUpClass("NSGlassEffectView").alloc().initWithFrame_(cadre)
        verre.setCornerRadius_(RAYON)
        verre.setContentView_(page)
        return verre
    except objc.nosuchclass_error:
        flou = NSVisualEffectView.alloc().initWithFrame_(cadre)
        flou.setMaterial_(6)  # NSVisualEffectMaterialPopover
        flou.setState_(1)  # actif même quand l'app n'a pas la main
        flou.setWantsLayer_(True)
        flou.layer().setCornerRadius_(RAYON)
        flou.layer().setMasksToBounds_(True)
        page.setFrame_(cadre)
        page.setAutoresizingMask_(18)  # largeur et hauteur suivent le fond
        flou.addSubview_(page)
        return flou


def accent_du_mac():
    """La couleur d'accent choisie dans les réglages du Mac, en #rrggbb."""
    c = NSColor.controlAccentColor().colorUsingColorSpace_(NSColorSpace.sRGBColorSpace())
    return "#%02x%02x%02x" % tuple(round(255 * v) for v in (c.redComponent(), c.greenComponent(), c.blueComponent()))


def corps_en_dict(corps):
    """NSDictionary -> dict Python. Passer par JSON garantit de vrais bool, str, int."""
    try:
        donnees, _ = NSJSONSerialization.dataWithJSONObject_options_error_(corps, 0, None)
        return json.loads(bytes(donnees))
    except Exception:
        return None


class Pont(NSObject, protocols=[objc.protocolNamed("WKScriptMessageHandler")]):
    def userContentController_didReceiveScriptMessage_(self, controleur, message):
        self.app.message_de_la_page(corps_en_dict(message.body()))


class App(NSObject):
    def applicationDidFinishLaunching_(self, _):
        self.page_prete = False
        self.releve = releve.lire()
        self.vu = self.signature_du_fichier()
        self.erreur = None
        self.absent = sonde.trouver_claude() is None
        self.actualisation = False
        # Avec l'actualisation automatique, la première part dès le lancement : sans Claude Code ouvert dans un
        # terminal, rien d'autre ne remplit le relevé, et la jauge resterait vide un quart d'heure.
        self.derniere_auto = time.monotonic() - AUTO
        self.hauteur = HAUTEUR_DEPART

        self.icone = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)
        bouton = self.icone.button()
        bouton.setImage_(icone_barre())
        bouton.setTarget_(self)
        bouton.setAction_("basculer:")

        config = WKWebViewConfiguration.alloc().init()
        self.pont = Pont.alloc().init()
        self.pont.app = self
        config.userContentController().addScriptMessageHandler_name_(self.pont, "pont")
        self.page = WKWebView.alloc().initWithFrame_configuration_(NSMakeRect(0, 0, LARGEUR, self.hauteur), config)
        self.page.setValue_forKey_(False, "drawsBackground")  # le verre du panneau passe au travers
        self.page.loadFileURL_allowingReadAccessToURL_(
            NSURL.fileURLWithPath_(str(DOSSIER_PAGE / "index.html")),
            NSURL.fileURLWithPath_isDirectory_(str(DOSSIER_PAGE), True),
        )

        self.panneau = Fenetre.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, LARGEUR + 2 * MARGE, self.hauteur + 2 * MARGE),
            NSWindowStyleMaskBorderless | NSWindowStyleMaskNonactivatingPanel,  # ne prend pas la main à l'app en cours
            NSBackingStoreBuffered,
            False,
        )
        self.panneau.setOpaque_(False)
        self.panneau.setBackgroundColor_(NSColor.clearColor())
        # Pas d'ombre de fenêtre : macOS la dessinerait sur le rectangle, d'où un cadre gris dans les coins arrondis
        # (leçon de Hue Controller). L'ombre est celle du verre, qui s'éteint dans la marge.
        self.panneau.setHasShadow_(False)
        self.panneau.setLevel_(NSPopUpMenuWindowLevel)
        cadre = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, LARGEUR + 2 * MARGE, self.hauteur + 2 * MARGE))
        self.fond = fond_en_verre(self.page, self.hauteur)
        self.fond.setFrameOrigin_((MARGE, MARGE))
        cadre.addSubview_(self.fond)
        self.panneau.setContentView_(cadre)
        # Un clic ailleurs referme le panneau (les clics dans nos propres fenêtres n'arrivent pas ici).
        self.guet = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
            NSEventMaskLeftMouseDown | NSEventMaskRightMouseDown, lambda _: self.panneau.orderOut_(None)
        )

        self.montrer()
        AppHelper.callLater(VEILLE, self.veiller)
        if ESSAI:
            AppHelper.callLater(1, self.basculer_, None)
            AppHelper.callLater(3, self.bilan)

    # --- L'état ---

    @objc.python_method
    def etat(self):
        prefs = {"demarrage": demarrage.actif(), "auto": reglages.charger()["auto"]}
        return releve.etat(self.releve, time.time(), actualisation=self.actualisation, erreur=self.erreur,
                           absent=self.absent, reglages=prefs)

    @objc.python_method
    def montrer(self):
        """Met à jour la barre de menus, et la page si elle est prête."""
        etat = self.etat()
        session = etat.get("session")
        pourcentage = session["pourcentage"] if session else None
        bouton = self.icone.button()
        texte = releve.titre(etat)
        attributs = {NSFontAttributeName: NSFont.monospacedDigitSystemFontOfSize_weight_(13, 0)}
        if releve.niveau(pourcentage) == "limite":
            attributs[NSForegroundColorAttributeName] = NSColor.systemRedColor()
        bouton.setAttributedTitle_(NSAttributedString.alloc().initWithString_attributes_((" " + texte) if texte else "", attributs))
        if self.page_prete:
            self.page.evaluateJavaScript_completionHandler_(f"window.recevoir({json.dumps(etat, ensure_ascii=False)})", None)

    @objc.python_method
    def signature_du_fichier(self):
        try:
            infos = releve.CHEMIN.stat()
            return (infos.st_mtime_ns, infos.st_size)
        except OSError:
            return None

    @objc.python_method
    def veiller(self):
        """Toutes les deux secondes : le relevé a-t-il changé sur le disque (la ligne d'état de Claude Code l'écrit) ?
        Le temps compte aussi : une fenêtre échue doit passer à 0 % sans attendre de relevé."""
        signature = self.signature_du_fichier()
        if signature != self.vu:
            self.vu = signature
            lu = releve.lire()
            if lu is not None:
                self.releve = lu
                self.erreur = None
        self.montrer()
        if reglages.charger()["auto"] and not self.actualisation and time.monotonic() - self.derniere_auto >= AUTO:
            self.actualiser()
        AppHelper.callLater(VEILLE, self.veiller)

    # --- L'actualisation à la demande ---

    @objc.python_method
    def actualiser(self):
        if self.actualisation or ESSAI:
            return
        self.actualisation = True
        self.derniere_auto = time.monotonic()
        self.montrer()
        threading.Thread(target=self.sonder, daemon=True).start()

    @objc.python_method
    def sonder(self):
        """Dans un fil à part : poser la question à Claude Code peut prendre plusieurs secondes."""
        erreur, absent, nouveau = None, False, None
        try:
            nouveau = sonde.relever()
        except sonde.ClaudeAbsent as exc:
            erreur, absent = str(exc), True
        except sonde.SondeErreur as exc:
            erreur = str(exc)
        except Exception as exc:  # le fil ne doit jamais mourir en silence
            print("erreur inattendue :", type(exc).__name__, flush=True)
            erreur = "Claude Code ne répond pas."
        AppHelper.callAfter(self.fin_de_sonde, nouveau, erreur, absent)

    @objc.python_method
    def fin_de_sonde(self, nouveau, erreur, absent):
        self.actualisation = False
        self.absent = absent
        self.erreur = erreur
        if nouveau is not None:
            self.releve = releve.fusionner(releve.lire(), nouveau)
            try:
                releve.ecrire(self.releve)
            except OSError:
                pass  # le relevé reste en mémoire ; il sera réécrit au prochain
            self.vu = self.signature_du_fichier()
        self.montrer()

    # --- Le panneau ---

    def basculer_(self, _):
        if self.panneau.isVisible():
            self.panneau.orderOut_(None)
            return
        self.placer()
        self.panneau.makeKeyAndOrderFront_(None)
        if self.page_prete:
            self.page.evaluateJavaScript_completionHandler_(f"window.accent({json.dumps(accent_du_mac())})", None)
        self.montrer()

    @objc.python_method
    def placer(self):
        """Centré sous l'icône, sans sortir de l'écran ; le haut du panneau reste collé sous la barre de menus."""
        icone = self.icone.button().window().frame()
        ecran = NSScreen.mainScreen().frame()
        x = min(max(icone.origin.x + icone.size.width / 2 - LARGEUR / 2, 8), ecran.size.width - LARGEUR - 8)
        self.panneau.setFrame_display_(
            NSMakeRect(x - MARGE, icone.origin.y - self.hauteur - ECART - MARGE, LARGEUR + 2 * MARGE, self.hauteur + 2 * MARGE), True)
        self.fond.setFrame_(NSMakeRect(MARGE, MARGE, LARGEUR, self.hauteur))

    @objc.python_method
    def message_de_la_page(self, message):
        if not isinstance(message, dict):
            return
        action = message.get("action")
        if action == "pret":
            self.page_prete = True
            self.page.evaluateJavaScript_completionHandler_(f"window.accent({json.dumps(accent_du_mac())})", None)
            self.montrer()
        elif action == "hauteur":
            px = message.get("px")
            # La page dit la hauteur de son contenu ; la fenêtre s'y ajuste, dans des bornes raisonnables.
            if isinstance(px, (int, float)) and not isinstance(px, bool) and 120 <= px <= HAUTEUR_MAXI and round(px) != self.hauteur:
                self.hauteur = round(px)
                if self.panneau.isVisible():
                    self.placer()
        elif action == "actualiser":
            self.actualiser()
        elif action == "auto" and isinstance(message.get("on"), bool):
            try:
                reglages.enregistrer({"auto": message["on"]})
            except OSError:
                pass
            self.derniere_auto = time.monotonic()
            self.montrer()
            if message["on"]:
                self.actualiser()  # cocher la case donne tout de suite des chiffres frais
        elif action == "demarrage" and isinstance(message.get("on"), bool):
            try:
                demarrage.activer() if message["on"] else demarrage.desactiver()
            except (RuntimeError, OSError):
                pass  # l'état renvoyé dira ce qu'il en est vraiment
            self.montrer()
        elif action == "auteur":
            # L'adresse est fixée ici : la page ne peut pas faire ouvrir autre chose.
            NSWorkspace.sharedWorkspace().openURL_(NSURL.URLWithString_(PAGE_AUTEUR))
        elif action == "quitter":
            NSApplication.sharedApplication().terminate_(None)

    @objc.python_method
    def bilan(self):
        etat = self.etat()
        print("panneau ouvert :", bool(self.panneau.isVisible()), "| page prête :", self.page_prete,
              "| état :", etat["etat"], "| barre de menus :", releve.titre(etat) or "(jauge seule)", "| hauteur :", self.hauteur, flush=True)
        AppHelper.stopEventLoop()


_VERROU = None  # gardé ouvert toute la vie de l'app


def principal():
    global _VERROU
    if not ESSAI:
        # Une seule app à la fois : sinon deux jauges dans la barre (lancement automatique + lancement à la main).
        releve.DOSSIER.mkdir(parents=True, exist_ok=True)
        _VERROU = open(releve.DOSSIER / "verrou", "w")
        try:
            fcntl.flock(_VERROU, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print("Claude Usage tourne déjà.")
            return
    application = NSApplication.sharedApplication()
    application.setActivationPolicy_(NSApplicationActivationPolicyAccessory)  # pas d'icône dans le Dock
    app = App.alloc().init()
    application.setDelegate_(app)
    AppHelper.runEventLoop()
