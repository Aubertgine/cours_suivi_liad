"""Connexion par identifiant et mot de passe.

Les comptes sont dans les secrets (jamais dans le code) :

    [utilisateurs.pierre-antoine]
    nom = "Pierre-Antoine"
    role = "prof"
    mot_de_passe = "pbkdf2_sha256$..."     # généré par outils/creer_mot_de_passe.py

Le mot de passe n'est jamais stocké en clair : on garde seulement son « empreinte ».
"""
import base64
import hashlib
import hmac
import os

ITERATIONS = 300_000


def empreinte(mot_de_passe, sel=None):
    """Transforme un mot de passe en empreinte : 'pbkdf2_sha256$iterations$sel$hash'."""
    sel = sel or os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", mot_de_passe.encode("utf-8"), sel, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${base64.b64encode(sel).decode()}${base64.b64encode(h).decode()}"


def verifier(mot_de_passe, empreinte_stockee):
    try:
        algo, iterations, sel, attendu = empreinte_stockee.split("$")
        h = hashlib.pbkdf2_hmac("sha256", mot_de_passe.encode("utf-8"),
                                base64.b64decode(sel), int(iterations))
        return hmac.compare_digest(base64.b64encode(h).decode(), attendu)
    except (ValueError, TypeError):
        return False


def connecter(utilisateurs, identifiant, mot_de_passe):
    """Renvoie le compte (dict avec identifiant, nom, role) si c'est bon, sinon None."""
    compte = utilisateurs.get(identifiant.strip().lower())
    if compte and verifier(mot_de_passe, compte.get("mot_de_passe", "")):
        return {"identifiant": identifiant.strip().lower(),
                "nom": compte.get("nom", identifiant), "role": compte.get("role", "eleve")}
    return None
