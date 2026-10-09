#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Position des astres par rapport aux constellations du zodiaque
Lieu : Antananarivo, Madagascar  |  Avec précession des équinoxes
Version Skyfield + éphéméride JPL DE440 (haute précision)

Installation :
    pip install skyfield numpy

Au premier lancement, Skyfield télécharge l'éphéméride DE440 (~114 Mo,
couvre 1550-2650) dans le dossier "donnees_skyfield". Pour un fichier plus
léger (~32 Mo, 1849-2150, même précision), mettez EPHEMERIDE = "de440s.bsp".

Le programme demande la date et l'heure locales d'Antananarivo (UTC+3).

Ce qui est calculé :
  - positions topocentriques (parallaxe lunaire incluse), apparentes
    (déviation de la lumière, aberration, temps de lumière) ;
  - constellation IAU (frontières officielles) de chaque astre ;
  - les 3 étoiles nommées les plus proches de l'astre dans sa constellation
    (catalogue intégré d'environ 110 étoiles, modifiable : ETOILES_NOMMEES) ;
  - signe du zodiaque tropical (équinoxe de la date) et sidéral (Lahiri) ;
  - précession des équinoxes (modèle IAU 2006, valable sur plusieurs millénaires).
"""
import math
import os
import sys
from datetime import datetime, timedelta, timezone

from skyfield.api import (
    Loader, wgs84, position_of_radec,
    load_constellation_map, load_constellation_names,
)
from skyfield.precessionlib import compute_precession

# ----------------------------------------------------------------------------
# 1. Configuration
# ----------------------------------------------------------------------------
EPHEMERIDE = "de440s.bsp"         # 1849-2150 ; "de440.bsp" pour 1550-2650


def _dossier_donnees() -> str:
    """Dossier des données Skyfield.
    - Exécutable PyInstaller : éphéméride embarquée si présente, sinon
      téléchargement à côté du .exe.
    - Script Python normal : dossier "donnees_skyfield" du répertoire courant."""
    if getattr(sys, "frozen", False):
        embarque = os.path.join(getattr(sys, "_MEIPASS", ""), "donnees_skyfield")
        if os.path.exists(os.path.join(embarque, EPHEMERIDE)):
            return embarque
        return os.path.join(os.path.dirname(sys.executable), "donnees_skyfield")
    return "donnees_skyfield"


DOSSIER_DONNEES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "donnees_skyfield")

# Antananarivo (WGS84)
LATITUDE, LONGITUDE, ALTITUDE_M = -18.9137, 47.5361, 1280.0
FUSEAU_H = 3                      # UTC+3

# Noms DE440 (barycentres pour Mars et au-delà : écart < 0,001" pour Jupiter
# et négligeable pour les autres ; Mercure/Vénus : barycentre = centre)
CORPS = [
    ("Soleil",  "sun"),
    ("Lune",    "moon"),
    ("Mercure", "mercury barycenter"),
    ("Vénus",   "venus barycenter"),
    ("Mars",    "mars barycenter"),
    ("Jupiter", "jupiter barycenter"),
    ("Saturne", "saturn barycenter"),
    ("Uranus",  "uranus barycenter"),
    ("Neptune", "neptune barycenter"),
]

SIGNES = ["Bélier", "Taureau", "Gémeaux", "Cancer", "Lion", "Vierge",
          "Balance", "Scorpion", "Sagittaire", "Capricorne", "Verseau", "Poissons"]

# Abréviation IAU -> français (autres constellations : nom anglais de Skyfield)
CONST_FR = {
    "Ari": "Bélier", "Tau": "Taureau", "Gem": "Gémeaux", "Cnc": "Cancer",
    "Leo": "Lion", "Vir": "Vierge", "Lib": "Balance", "Sco": "Scorpion",
    "Oph": "Ophiuchus", "Sgr": "Sagittaire", "Cap": "Capricorne",
    "Aqr": "Verseau", "Psc": "Poissons", "Cet": "Baleine", "Sex": "Sextant",
    "Ori": "Orion", "Hya": "Hydre", "Crt": "Coupe", "Crv": "Corbeau",
    "CMi": "Petit Chien", "Lup": "Loup", "Ser": "Serpent", "Eri": "Éridan",
    "Lep": "Lièvre", "Mon": "Licorne", "Aql": "Aigle", "Del": "Dauphin",
}

# Ayanamsa de Lahiri à J2000 : 23°51'11" (l'ayanamsa croît ensuite avec la précession)
AYANAMSA_LAHIRI_J2000 = 23.85306  # degrés


# ----------------------------------------------------------------------------
# 1b. Catalogue d'étoiles nommées (coordonnées J2000, mouvement propre ignoré)
# ----------------------------------------------------------------------------
# (nom, désignation de Bayer, ascension droite "h m s", déclinaison "° ' \"")
# La constellation de chaque étoile n'est pas écrite ici : elle est calculée
# au lancement avec les frontières IAU officielles de Skyfield.
ETOILES_NOMMEES = [
    # Bélier
    ("Hamal", "α Ari", "02 07 10.4", "+23 27 45"),
    ("Sheratan", "β Ari", "01 54 38.4", "+20 48 29"),
    ("Mesarthim", "γ Ari", "01 53 31.8", "+19 17 45"),
    # Taureau
    ("Aldébaran", "α Tau", "04 35 55.2", "+16 30 33"),
    ("Elnath", "β Tau", "05 26 17.5", "+28 36 27"),
    ("Alcyone (Pléiades)", "η Tau", "03 47 29.1", "+24 06 19"),
    ("Atlas (Pléiades)", "27 Tau", "03 49 09.7", "+24 03 12"),
    ("Maïa (Pléiades)", "20 Tau", "03 45 49.6", "+24 22 04"),
    ("Mérope (Pléiades)", "23 Tau", "03 46 19.6", "+23 56 54"),
    ("Électre (Pléiades)", "17 Tau", "03 44 52.5", "+24 06 48"),
    ("Taygète (Pléiades)", "19 Tau", "03 45 12.5", "+24 28 02"),
    ("Ain", "ε Tau", "04 28 37.0", "+19 10 50"),
    ("Hyadum I", "γ Tau", "04 19 47.6", "+15 37 40"),
    ("Hyadum II", "δ1 Tau", "04 22 56.1", "+17 32 33"),
    ("Tianguan", "ζ Tau", "05 37 38.7", "+21 08 33"),
    # Gémeaux
    ("Castor", "α Gem", "07 34 36.0", "+31 53 18"),
    ("Pollux", "β Gem", "07 45 18.9", "+28 01 34"),
    ("Alhena", "γ Gem", "06 37 42.7", "+16 23 57"),
    ("Mebsuta", "ε Gem", "06 43 55.9", "+25 07 52"),
    ("Tejat", "μ Gem", "06 22 57.6", "+22 30 49"),
    ("Propus", "η Gem", "06 14 52.7", "+22 30 24"),
    ("Wasat", "δ Gem", "07 20 07.4", "+21 58 56"),
    ("Mekbuda", "ζ Gem", "07 04 06.5", "+20 34 13"),
    ("Alzirr", "ξ Gem", "06 45 17.4", "+12 53 44"),
    # Cancer
    ("Acubens", "α Cnc", "08 58 29.2", "+11 51 28"),
    ("Altarf", "β Cnc", "08 16 30.9", "+09 11 08"),
    ("Asellus Australis", "δ Cnc", "08 44 41.1", "+18 09 15"),
    ("Asellus Borealis", "γ Cnc", "08 43 17.2", "+21 28 07"),
    ("Praesepe (la Crèche)", "M44", "08 40 24.0", "+19 40 00"),
    # Lion
    ("Régulus", "α Leo", "10 08 22.3", "+11 58 02"),
    ("Denebola", "β Leo", "11 49 03.6", "+14 34 19"),
    ("Algieba", "γ Leo", "10 19 58.4", "+19 50 30"),
    ("Zosma", "δ Leo", "11 14 06.5", "+20 31 25"),
    ("Chertan", "θ Leo", "11 14 14.4", "+15 25 46"),
    ("Adhafera", "ζ Leo", "10 16 41.4", "+23 25 02"),
    ("Rasalas", "μ Leo", "09 52 45.8", "+26 00 25"),
    ("Algenubi", "ε Leo", "09 45 51.1", "+23 46 27"),
    # Vierge
    ("Spica", "α Vir", "13 25 11.6", "-11 09 41"),
    ("Vindemiatrix", "ε Vir", "13 02 10.6", "+10 57 33"),
    ("Porrima", "γ Vir", "12 41 39.6", "-01 26 58"),
    ("Zavijava", "β Vir", "11 50 41.7", "+01 45 53"),
    ("Zaniah", "η Vir", "12 19 54.4", "-00 40 00"),
    ("Heze", "ζ Vir", "13 34 41.6", "-00 35 45"),
    ("Syrma", "ι Vir", "14 16 00.9", "-06 00 02"),
    ("Auva", "δ Vir", "12 55 36.2", "+03 23 51"),
    # Balance
    ("Zubeneschamali", "β Lib", "15 17 00.4", "-09 22 59"),
    ("Zubenelgenubi", "α2 Lib", "14 50 52.7", "-16 02 30"),
    ("Zubenelhakrabi", "γ Lib", "15 35 31.6", "-14 47 23"),
    ("Brachium", "σ Lib", "15 04 04.2", "-25 16 55"),
    # Scorpion
    ("Antarès", "α Sco", "16 29 24.5", "-26 25 55"),
    ("Shaula", "λ Sco", "17 33 36.5", "-37 06 14"),
    ("Sargas", "θ Sco", "17 37 19.1", "-42 59 52"),
    ("Dschubba", "δ Sco", "16 00 20.0", "-22 37 18"),
    ("Acrab", "β1 Sco", "16 05 26.2", "-19 48 19"),
    ("Wei", "ε Sco", "16 50 09.8", "-34 17 36"),
    ("Lesath", "υ Sco", "17 30 45.8", "-37 17 45"),
    ("Alniyat", "σ Sco", "16 21 11.3", "-25 35 34"),
    ("Girtab", "κ Sco", "17 42 29.3", "-39 01 48"),
    ("Jabbah", "ν Sco", "16 11 59.7", "-19 27 38"),
    ("Fang", "π Sco", "15 58 51.1", "-26 06 51"),
    # Ophiuchus
    ("Rasalhague", "α Oph", "17 34 56.1", "+12 33 36"),
    ("Sabik", "η Oph", "17 10 22.7", "-15 43 30"),
    ("Cebalrai", "β Oph", "17 43 28.4", "+04 34 02"),
    ("Yed Prior", "δ Oph", "16 14 20.7", "-03 41 40"),
    ("Yed Posterior", "ε Oph", "16 18 19.3", "-04 41 33"),
    ("Han", "ζ Oph", "16 37 09.5", "-10 34 02"),
    ("Marfik", "λ Oph", "16 30 54.8", "+01 59 02"),
    ("Sinistra", "ν Oph", "17 59 01.6", "-09 46 25"),
    # Sagittaire
    ("Kaus Australis", "ε Sgr", "18 24 10.3", "-34 23 05"),
    ("Kaus Media", "δ Sgr", "18 20 59.6", "-29 49 41"),
    ("Kaus Borealis", "λ Sgr", "18 27 58.2", "-25 25 18"),
    ("Nunki", "σ Sgr", "18 55 15.9", "-26 17 48"),
    ("Ascella", "ζ Sgr", "19 02 36.7", "-29 52 49"),
    ("Alnasl", "γ2 Sgr", "18 05 48.5", "-30 25 27"),
    ("Arkab Prior", "β1 Sgr", "19 22 38.3", "-44 27 32"),
    ("Rukbat", "α Sgr", "19 23 53.2", "-40 36 57"),
    ("Albaldah", "π Sgr", "19 09 45.8", "-21 01 25"),
    # Capricorne
    ("Deneb Algedi", "δ Cap", "21 47 02.4", "-16 07 38"),
    ("Dabih", "β Cap", "20 21 00.7", "-14 46 53"),
    ("Algedi", "α2 Cap", "20 18 03.3", "-12 32 41"),
    ("Nashira", "γ Cap", "21 40 05.5", "-16 39 44"),
    # Verseau
    ("Sadalsuud", "β Aqr", "21 31 33.5", "-05 34 16"),
    ("Sadalmelik", "α Aqr", "22 05 47.0", "-00 19 11"),
    ("Sadachbia", "γ Aqr", "22 21 39.4", "-01 23 15"),
    ("Skat", "δ Aqr", "22 54 39.0", "-15 49 15"),
    ("Albali", "ε Aqr", "20 47 40.6", "-09 29 45"),
    # Poissons
    ("Alrescha", "α Psc", "02 02 02.8", "+02 45 49"),
    ("Alpherg", "η Psc", "01 31 29.0", "+15 20 45"),
    ("Fumalsamakah", "β Psc", "23 03 52.6", "+03 49 12"),
    # Baleine
    ("Menkar", "α Cet", "03 02 16.8", "+04 05 23"),
    ("Diphda", "β Cet", "00 43 35.4", "-17 59 12"),
    ("Mira", "ο Cet", "02 19 20.8", "-02 58 39"),
    ("Kaffaljidhma", "γ Cet", "02 43 18.0", "+03 14 09"),
    ("Baten Kaitos", "ζ Cet", "01 51 27.6", "-10 20 06"),
    # Orion
    ("Bételgeuse", "α Ori", "05 55 10.3", "+07 24 25"),
    ("Rigel", "β Ori", "05 14 32.3", "-08 12 06"),
    ("Bellatrix", "γ Ori", "05 25 07.9", "+06 20 59"),
    ("Alnilam", "ε Ori", "05 36 12.8", "-01 12 07"),
    ("Alnitak", "ζ Ori", "05 40 45.5", "-01 56 34"),
    ("Mintaka", "δ Ori", "05 32 00.4", "-00 17 57"),
    ("Saiph", "κ Ori", "05 47 45.4", "-09 40 11"),
    ("Meissa", "λ Ori", "05 35 08.3", "+09 56 03"),
    # Autres constellations proches de l'écliptique
    ("Alphard", "α Hya", "09 27 35.2", "-08 39 31"),
    ("Procyon", "α CMi", "07 39 18.1", "+05 13 30"),
    ("Gomeisa", "β CMi", "07 27 09.0", "+08 17 22"),
    ("Arneb", "α Lep", "05 32 43.8", "-17 49 20"),
    ("Gienah", "γ Crv", "12 15 48.4", "-17 32 31"),
    ("Algorab", "δ Crv", "12 29 51.9", "-16 30 56"),
    ("Kraz", "β Crv", "12 34 23.2", "-23 23 48"),
    ("Alchiba", "α Crv", "12 08 24.8", "-24 43 44"),
    ("Alkes", "α Crt", "10 59 46.4", "-18 17 56"),
    ("Unukalhai", "α Ser", "15 44 16.1", "+06 25 32"),
]
N_ETOILES = 3   # nombre d'étoiles proches affichées par astre


def _ra_heures(s: str) -> float:
    h, m, sec = s.split()
    return int(h) + int(m) / 60.0 + float(sec) / 3600.0


def _dec_degres(s: str) -> float:
    d, m, sec = s.split()
    signe = -1.0 if d.startswith("-") else 1.0
    return signe * (abs(int(d)) + int(m) / 60.0 + float(sec) / 3600.0)


def preparer_catalogue(constellation_de) -> list:
    """Convertit le catalogue en (nom, bayer, AD_h, Déc_deg, abbr_constellation)."""
    out = []
    for nom, bayer, ra_s, dec_s in ETOILES_NOMMEES:
        ra_h, dec = _ra_heures(ra_s), _dec_degres(dec_s)
        out.append((nom, bayer, ra_h, dec, constellation_de(position_of_radec(ra_h, dec))))
    return out


def separation_deg(ra1_h, dec1, ra2_h, dec2) -> float:
    """Distance angulaire (degrés) entre deux points (formule de Vincenty)."""
    a1, a2 = math.radians(ra1_h * 15.0), math.radians(ra2_h * 15.0)
    d1, d2 = math.radians(dec1), math.radians(dec2)
    dl = a2 - a1
    num = math.hypot(math.cos(d2) * math.sin(dl),
                     math.cos(d1) * math.sin(d2) - math.sin(d1) * math.cos(d2) * math.cos(dl))
    den = math.sin(d1) * math.sin(d2) + math.cos(d1) * math.cos(d2) * math.cos(dl)
    return math.degrees(math.atan2(num, den))


def etoiles_proches(ra_h, dec, abbr, catalogue, n=N_ETOILES):
    """Les n étoiles nommées les plus proches de l'astre, prises dans la
    constellation où il se trouve. Si le catalogue n'en contient aucune dans
    cette constellation, on prend les plus proches toutes constellations
    confondues. Renvoie (dans_la_constellation, [(séparation, étoile), ...])."""
    meme = [e for e in catalogue if e[4] == abbr]
    reserve = meme or catalogue
    classees = sorted(((separation_deg(ra_h, dec, e[2], e[3]), e) for e in reserve),
                      key=lambda x: x[0])
    return bool(meme), classees[:n]


# ----------------------------------------------------------------------------
# 2. Précession des équinoxes (IAU 2006, Capitaine et al.)
# ----------------------------------------------------------------------------
def _siecles(t) -> float:
    """Siècles juliens depuis J2000 (TT)."""
    return (t.tt - 2451545.0) / 36525.0


def precession_en_longitude(t) -> float:
    """Précession générale en longitude p_A (degrés) depuis J2000 : de combien
    l'équinoxe a reculé le long de l'écliptique."""
    T = _siecles(t)
    p = T * (5028.796195 + T * (1.1054348 + T * (0.00007964
        + T * (-0.000023857 + T * -0.0000000383))))
    return p / 3600.0


def vitesse_precession_arcsec_an(t) -> float:
    """Vitesse instantanée de la précession en longitude (secondes d'arc/an)."""
    T = _siecles(t)
    dp = (5028.796195 + T * (2 * 1.1054348 + T * (3 * 0.00007964
          + T * (4 * -0.000023857 + T * 5 * -0.0000000383))))
    return dp / 100.0


def ayanamsa(t) -> float:
    """Ayanamsa de Lahiri (degrés) à la date t."""
    return AYANAMSA_LAHIRI_J2000 + precession_en_longitude(t)


def point_vernal_radec_j2000(t):
    """Coordonnées (AD en heures, Déc. en degrés) dans le repère J2000 du point
    vernal de la date t (intersection équateur/écliptique de la date)."""
    P = compute_precession(t.tdb)           # J2000 -> équateur moyen de la date
    v = P[0]                                # axe x de la date exprimé en J2000
    ra = math.atan2(v[1], v[0]) % (2 * math.pi)
    dec = math.asin(max(-1.0, min(1.0, v[2])))
    return ra * 12.0 / math.pi, math.degrees(dec)


# ----------------------------------------------------------------------------
# 3. Utilitaires d'affichage
# ----------------------------------------------------------------------------
def deg_dms(x: float) -> str:
    s = "-" if x < 0 else "+"
    x = abs(x)
    d = int(x); m = int((x - d) * 60); sec = ((x - d) * 60 - m) * 60
    return f"{s}{d:02d}°{m:02d}'{sec:04.1f}\""


def heure_hms(h: float) -> str:
    h %= 24
    hh = int(h); mm = int((h - hh) * 60); ss = ((h - hh) * 60 - mm) * 60
    return f"{hh:02d}h{mm:02d}m{ss:04.1f}s"


# ----------------------------------------------------------------------------
# 4. Saisie de la date et de l'heure
# ----------------------------------------------------------------------------
def demander_date_heure(ts):
    """Demande la date/heure LOCALES d'Antananarivo, les valide et renvoie un
    objet Time Skyfield (UTC). Entrée vide = moment présent."""
    maintenant = datetime.now(timezone(timedelta(hours=FUSEAU_H)))
    print("Entrez la date et l'heure locales d'Antananarivo (UTC+3).")
    print("Laissez vide pour utiliser le moment présent.\n")
    while True:
        d = input(f"Date (JJ/MM/AAAA) [{maintenant:%d/%m/%Y}] : ").strip()
        h = input(f"Heure (HH:MM ou HH:MM:SS) [{maintenant:%H:%M}] : ").strip()
        d = d or f"{maintenant:%d/%m/%Y}"
        h = (h or f"{maintenant:%H:%M}").replace("h", ":").replace("H", ":")
        local = None
        for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
            try:
                local = datetime.strptime(f"{d} {h}", fmt)
                break
            except ValueError:
                pass
        if local is None:
            print("  Format invalide, recommencez (ex. 08/10/2026 et 09:41).\n")
            continue
        u = local - timedelta(hours=FUSEAU_H)
        return ts.utc(u.year, u.month, u.day, u.hour, u.minute, u.second)


def demander_continuer() -> bool:
    """Demande s'il faut recommencer avec une autre date. Renvoie True si oui."""
    while True:
        r = input("\nVoulez-vous continuer avec une autre date ? [Y/N] : ").strip().lower()
        if r in ("y", "yes", "o", "oui"):
            return True
        if r in ("n", "no", "non"):
            return False
        print("  Réponse invalide : tapez Y (oui) ou N (non).")


# ----------------------------------------------------------------------------
# 5. Calcul et affichage
# ----------------------------------------------------------------------------
def main():
    load = Loader(DOSSIER_DONNEES)
    ts = load.timescale()
    print(f"Chargement de l'éphéméride {EPHEMERIDE} (téléchargement au premier lancement)...")
    eph = load(EPHEMERIDE)
    constellation_de = load_constellation_map()
    noms_en = dict(load_constellation_names())

    def nom_abbr(abbr: str) -> str:
        return CONST_FR.get(abbr, noms_en.get(abbr, abbr))

    def nom_const(position) -> str:
        return nom_abbr(constellation_de(position))

    catalogue = preparer_catalogue(constellation_de)

    earth = eph["earth"]
    lieu = wgs84.latlon(LATITUDE, LONGITUDE, elevation_m=ALTITUDE_M)
    observateur = earth + lieu

    while True:
        print()
        t = demander_date_heure(ts)
        local = t.utc_datetime() + timedelta(hours=FUSEAU_H)
        tsl = (t.gast + LONGITUDE / 15.0) % 24.0

        print()
        print("=" * 100)
        print(f" Antananarivo (lat {LATITUDE:.4f}°, lon {LONGITUDE:.4f}°, alt {ALTITUDE_M:.0f} m)"
              f"  |  éphéméride {EPHEMERIDE}")
        print(f" Date : {t.utc_strftime('%Y-%m-%d %H:%M:%S')} UTC  |  "
              f"{local:%Y-%m-%d %H:%M:%S} heure locale (UTC+{FUSEAU_H})")
        print(f" Temps sidéral local apparent : {heure_hms(tsl)}")
        print("=" * 100)
        print(f"{'Astre':<9}{'AD (J2000)':>13}{'Décl.':>13}{'Hauteur':>10}{'Azimut':>9}"
              f"  {'Constellation':<13}{'Zod. tropical':<19}{'Zod. sidéral (Lahiri)'}")
        print("-" * 100)

        aya = ayanamsa(t)
        obs_t = observateur.at(t)
        resultats = []   # (nom, AD_h, Déc_deg, abréviation de constellation)
        for nom, cle in CORPS:
            astro = obs_t.observe(eph[cle])            # topocentrique, avec temps de lumière
            app = astro.apparent()                     # + déviation de la lumière, aberration
            ra, dec, _ = astro.radec()                 # J2000 (repère des constellations)
            alt, az, _ = app.altaz()                   # hauteur géométrique (sans réfraction)
            _, lon_e, _ = app.ecliptic_latlon("date")  # écliptique et équinoxe de la date

            lon_trop = lon_e.degrees % 360.0
            lon_sid = (lon_trop - aya) % 360.0
            trop = f"{lon_trop % 30:5.2f}° {SIGNES[int(lon_trop // 30)]}"
            sid = f"{lon_sid % 30:5.2f}° {SIGNES[int(lon_sid // 30)]}"
            etat = "" if alt.degrees > 0 else "  (sous l'horizon)"
            abbr = constellation_de(astro)
            resultats.append((nom, ra.hours, dec.degrees, abbr))
            print(f"{nom:<9}{heure_hms(ra.hours):>13}{deg_dms(dec.degrees):>13}"
                  f"{alt.degrees:>9.2f}°{az.degrees:>8.1f}°  {nom_abbr(abbr):<13}{trop:<19}{sid}{etat}")

        # --- Étoiles nommées les plus proches de chaque astre ---
        print()
        print("ÉTOILES NOMMÉES LES PLUS PROCHES (dans la constellation de l'astre)")
        print("-" * 100)
        for nom, ra_h, dec_d, abbr in resultats:
            dans, proches = etoiles_proches(ra_h, dec_d, abbr, catalogue)
            entete = f" {nom} - {nom_abbr(abbr)}"
            if not dans:
                entete += " (aucune étoile nommée du catalogue ici ; plus proches voisines :)"
            print(entete)
            for sep, e in proches:
                voisine = "" if dans else f" [{nom_abbr(e[4])}]"
                print(f"     {e[0]} ({e[1]}){voisine} : {sep:.1f}°")

        # --- Précession des équinoxes ---
        print()
        print("PRÉCESSION DES ÉQUINOXES (IAU 2006)")
        print("-" * 100)
        prec = precession_en_longitude(t)
        vit = vitesse_precession_arcsec_an(t)
        print(f" Recul du point vernal depuis J2000 : {prec:.4f}° ({deg_dms(prec)[1:]})")
        print(f" Ayanamsa de Lahiri                 : {deg_dms(aya)[1:]}")
        print(f" Vitesse de précession              : {vit:.3f}\"/an  (cycle complet ≈ {360 * 3600 / vit:,.0f} ans)"
              .replace(",", " "))
        ra_v, dec_v = point_vernal_radec_j2000(t)
        print(f" Point vernal (équinoxe de mars) dans la constellation : "
              f"{nom_const(position_of_radec(ra_v, dec_v))}")
        print()
        print(" Constellation du point vernal à travers les âges :")
        for an in (-4000, -2000, -1000, 0, 1000, 2000, 2026, 2600, 3000, 4000):
            ra_v, dec_v = point_vernal_radec_j2000(ts.J(an))
            print(f"   {an:>6} : {nom_const(position_of_radec(ra_v, dec_v))}")
        print()
        print(" Note : le zodiaque tropical (signes de 30° depuis l'équinoxe) dérive")
        print(" de ~24° par rapport aux constellations à cause de la précession.")

        if not demander_continuer():
            break
        print()


if __name__ == "__main__":
    # Console Windows : accents et symboles (°, α, β...) corrects
    for flux in (sys.stdout, sys.stderr):
        try:
            flux.reconfigure(encoding="utf-8")
        except Exception:
            pass
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\nErreur : {e}")
        print("Sans éphéméride embarquée, une connexion Internet est nécessaire au 1er lancement.")
    finally:
        input("\nAppuyez sur Entrée pour fermer...")
