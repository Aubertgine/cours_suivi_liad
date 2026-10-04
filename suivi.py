"""Données et calculs du suivi : séances données, virements reçus, solde.

Le stockage (fichiers sur le PC ou Supabase en ligne) est géré par stockage.py.
"""
import uuid
from datetime import datetime

from stockage import en_cache, magasin, nom_de_fichier_sur, vider_cache

TYPES_DOCUMENTS = ["pdf", "png", "jpg", "jpeg"]


def nouvel_id():
    """Identifiant court et unique, ex. 'a3f9c2d1'."""
    return uuid.uuid4().hex[:8]


# ---------- Séances ----------

def lire_seances():
    seances = en_cache("seances", lambda: magasin().lister("seances"))
    return sorted(seances, key=lambda s: (s["date"], s["debut"]))


def ajouter_seance(date, debut, fin, tarif_horaire, notion=""):
    magasin().inserer("seances", {"id": nouvel_id(), "date": date, "debut": debut, "fin": fin,
                                  "tarif_horaire": tarif_horaire, "notion": notion})
    vider_cache()


def modifier_seance(id_, date, debut, fin, tarif_horaire, notion=""):
    magasin().modifier("seances", id_, {"id": id_, "date": date, "debut": debut, "fin": fin,
                                        "tarif_horaire": tarif_horaire, "notion": notion})
    vider_cache()


def supprimer_seance(id_):
    """Supprime la séance ET ses documents joints."""
    magasin().supprimer_tous_documents(id_)
    magasin().supprimer("seances", id_)
    vider_cache()


def duree_heures(s):
    fmt = "%H:%M"
    delta = datetime.strptime(s["fin"], fmt) - datetime.strptime(s["debut"], fmt)
    return delta.seconds / 3600


def montant(s):
    return round(duree_heures(s) * float(s["tarif_horaire"]), 2)


# ---------- Versements (virements reçus) ----------

def lire_versements():
    versements = en_cache("versements", lambda: magasin().lister("versements"))
    return sorted(versements, key=lambda v: v["date"])


def ajouter_versement(date, montant_recu, note=""):
    magasin().inserer("versements", {"id": nouvel_id(), "date": date, "montant": montant_recu, "note": note})
    vider_cache()


def modifier_versement(id_, date, montant_recu, note=""):
    magasin().modifier("versements", id_, {"id": id_, "date": date, "montant": montant_recu, "note": note})
    vider_cache()


def supprimer_versement(id_):
    magasin().supprimer("versements", id_)
    vider_cache()


# ---------- Documents joints ----------

def lister_documents(id_seance):
    return en_cache(f"docs_{id_seance}", lambda: magasin().lister_documents(id_seance))


def ajouter_document(id_seance, nom, contenu):
    """Enregistre un fichier joint. Si un fichier du même nom existe, ajoute (2), (3)…"""
    nom = nom_de_fichier_sur(nom)
    existants = set(magasin().lister_documents(id_seance))
    base, point, ext = nom.rpartition(".")
    if not point:
        base, ext = nom, ""
    candidat, n = nom, 2
    while candidat in existants:
        candidat = f"{base} ({n}){point}{ext}"
        n += 1
    magasin().deposer_document(id_seance, candidat, contenu)
    vider_cache()


def ouvrir_document(id_seance, nom):
    """Renvoie ("lien", url) en ligne, ou ("octets", contenu) en local."""
    return en_cache(f"ouvrir_{id_seance}_{nom}", lambda: magasin().ouvrir_document(id_seance, nom))


def supprimer_document(id_seance, nom):
    magasin().supprimer_document(id_seance, nom)
    vider_cache()


# ---------- Calculs ----------

def total_seances():
    return round(sum(montant(s) for s in lire_seances()), 2)


def total_versements():
    return round(sum(float(v["montant"]) for v in lire_versements()), 2)


def solde():
    """Positif : on te doit de l'argent. Négatif : tu as reçu une avance. 0 : tout est réglé."""
    return round(total_seances() - total_versements(), 2)


def statut_seances():
    """Répartit l'argent reçu sur les séances, de la plus ancienne à la plus récente.
    Renvoie une liste de (seance, statut, reste_a_payer), dans l'ordre chronologique."""
    disponible = total_versements()
    resultat = []
    for s in lire_seances():
        m = montant(s)
        if disponible >= m - 0.005:          # assez d'argent pour couvrir toute la séance
            resultat.append((s, "réglée", 0.0))
            disponible = round(disponible - m, 2)
        elif disponible > 0:                 # seulement une partie
            resultat.append((s, "partielle", round(m - disponible, 2)))
            disponible = 0.0
        else:                                # rien pour cette séance
            resultat.append((s, "en attente", m))
    return resultat


def historique():
    """Séances et versements mélangés par date, avec le solde après chaque ligne.
    Le même jour, la séance est placée avant le versement."""
    evenements = []
    for s in lire_seances():
        evenements.append({"date": s["date"], "ordre": (0, s["debut"]),
                           "libelle": f"Séance {s['debut']}–{s['fin']} ({duree_texte(s)})",
                           "montant": montant(s)})
    for v in lire_versements():
        libelle = "Virement reçu" + (f" – {v['note']}" if v["note"] else "")
        evenements.append({"date": v["date"], "ordre": (1, ""),
                           "libelle": libelle, "montant": -float(v["montant"])})
    evenements.sort(key=lambda e: (e["date"], e["ordre"]))
    courant = 0.0
    for e in evenements:
        courant = round(courant + e["montant"], 2)
        e["solde"] = courant
    return evenements


def revenu_cumule():
    """Pour le graphe : un point par date de séance, avec le cumul déjà reçu et le cumul en attente."""
    points = {}
    recu = attente = 0.0
    for s, statut, reste in statut_seances():
        m = montant(s)
        recu += m - reste
        attente += reste
        points[s["date"]] = (round(recu, 2), round(attente, 2))
    return [(d, r, a) for d, (r, a) in sorted(points.items())]


# ---------- Mise en forme ----------

def euros(x):
    """1234.5 -> '1 234,50 €' (format français)."""
    return f"{x:,.2f} €".replace(",", " ").replace(".", ",")


def date_fr(iso):
    """'2026-09-30' -> '30/09/2026'."""
    return datetime.strptime(iso, "%Y-%m-%d").strftime("%d/%m/%Y")


JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
        "août", "septembre", "octobre", "novembre", "décembre"]
MOIS_COURTS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.",
               "août", "sept.", "oct.", "nov.", "déc."]


def date_longue(iso):
    """'2026-09-30' -> 'Mercredi 30 septembre 2026'."""
    d = datetime.strptime(iso, "%Y-%m-%d")
    return f"{JOURS[d.weekday()].capitalize()} {d.day} {MOIS[d.month - 1]} {d.year}"


def date_courte(iso):
    """'2026-09-30' -> '30 sept.'."""
    d = datetime.strptime(iso, "%Y-%m-%d")
    return f"{d.day} {MOIS_COURTS[d.month - 1]}"


def duree_texte(s):
    """1.5 h -> '1 h 30' ; 1 h -> '1 h'."""
    minutes = round(duree_heures(s) * 60)
    h, m = divmod(minutes, 60)
    return f"{h} h {m:02d}" if m else f"{h} h"
