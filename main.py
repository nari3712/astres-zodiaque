# -*- coding: utf-8 -*-
"""Application Android (Kivy) : positions des astres et constellations du zodiaque.
Réutilise le calcul de astres_zodiaque_skyfield.py sans le modifier."""
import builtins
import contextlib
import io
import threading
from datetime import datetime, timedelta, timezone

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

import astres_zodiaque_skyfield as zod

POLICE = "data/fonts/RobotoMono-Regular.ttf"   # police à chasse fixe fournie par Kivy


def calculer(date_txt: str, heure_txt: str) -> str:
    """Exécute le calcul pour la date/heure locales (UTC+3) et renvoie le texte."""
    reponses = iter([date_txt, heure_txt, "n"])     # date, heure, "ne pas continuer"
    ancien_input = builtins.input
    builtins.input = lambda *_a, **_k: next(reponses)
    tampon = io.StringIO()
    try:
        with contextlib.redirect_stdout(tampon):
            zod.main()
    except Exception as e:
        tampon.write(f"\nErreur : {e}\n")
    finally:
        builtins.input = ancien_input
    return tampon.getvalue()


class AstresApp(App):
    title = "Astres & Zodiaque"

    def build(self):
        maintenant = datetime.now(timezone(timedelta(hours=zod.FUSEAU_H)))
        racine = BoxLayout(orientation="vertical", padding=8, spacing=6)

        haut = BoxLayout(size_hint_y=None, height=96, spacing=6)
        self.champ_date = TextInput(text=f"{maintenant:%d/%m/%Y}", multiline=False,
                                    hint_text="JJ/MM/AAAA", font_size="18sp")
        self.champ_heure = TextInput(text=f"{maintenant:%H:%M}", multiline=False,
                                     hint_text="HH:MM", font_size="18sp")
        bouton = Button(text="Calculer", font_size="18sp", size_hint_x=0.7)
        bouton.bind(on_release=self.lancer)
        for w in (self.champ_date, self.champ_heure, bouton):
            haut.add_widget(w)
        racine.add_widget(Label(text="Antananarivo - date/heure locales (UTC+3)",
                                size_hint_y=None, height=32, font_size="14sp"))
        racine.add_widget(haut)

        self.sortie = Label(text="Appuyez sur « Calculer ».", font_name=POLICE,
                            font_size="9sp", size_hint=(None, None), halign="left",
                            valign="top", markup=False)
        self.sortie.bind(texture_size=self._ajuster)
        self.defil = ScrollView(do_scroll_x=True, do_scroll_y=True, bar_width=6)
        self.defil.add_widget(self.sortie)
        racine.add_widget(self.defil)
        return racine

    def _ajuster(self, label, taille):
        label.size = taille
        label.text_size = (None, None)

    def lancer(self, *_):
        self.sortie.text = ("Calcul en cours...\n(1er lancement : chargement de "
                            "l'éphéméride, quelques secondes)")
        d, h = self.champ_date.text.strip(), self.champ_heure.text.strip()
        threading.Thread(target=self._travail, args=(d, h), daemon=True).start()

    def _travail(self, d, h):
        texte = calculer(d, h)
        Clock.schedule_once(lambda _dt: setattr(self.sortie, "text", texte))


if __name__ == "__main__":
    AstresApp().run()
