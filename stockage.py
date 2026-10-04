"""Où sont rangées les données.

Deux « magasins » interchangeables, avec exactement les mêmes fonctions :
- MagasinLocal    : fichiers CSV + dossier documents/ sur le PC (dossier donnees/).
- MagasinSupabase : base de données + stockage de fichiers en ligne (Supabase).

Le choix est automatique : si les secrets contiennent une section [supabase],
on utilise Supabase ; sinon on reste en local.
"""
import copy
import csv
import re
import time
import unicodedata
from pathlib import Path

import requests

RACINE = Path(__file__).parent
CHAMPS = {
    "seances": ["id", "date", "debut", "fin", "tarif_horaire", "notion"],
    "versements": ["id", "date", "montant", "note"],
}


def nom_de_fichier_sur(nom):
    """'Contrôle n°2 : énoncé.pdf' -> 'Controle n2 _ enonce.pdf' (sans accents ni caractères spéciaux)."""
    nom = unicodedata.normalize("NFKD", Path(nom).name).encode("ascii", "ignore").decode()
    nom = re.sub(r"[^A-Za-z0-9._ ()-]", "_", nom).strip() or "document"
    return nom


def lire_secrets():
    """Lit les secrets : d'abord via Streamlit (site en ligne), sinon le fichier .streamlit/secrets.toml."""
    try:
        import streamlit as st
        return {k: (dict(v) if hasattr(v, "keys") else v) for k, v in st.secrets.items()}
    except Exception:
        fichier = RACINE / ".streamlit" / "secrets.toml"
        if fichier.exists():
            import tomllib
            return tomllib.loads(fichier.read_text(encoding="utf-8"))
        return {}


# ======================================================================
# Magasin local (CSV)
# ======================================================================

class MagasinLocal:
    nom = "local"

    def __init__(self, dossier=RACINE / "donnees"):
        self.dossier = Path(dossier)
        self.documents = self.dossier / "documents"

    def _fichier(self, table):
        return self.dossier / f"{table}.csv"

    def _ecrire(self, table, lignes):
        self.dossier.mkdir(parents=True, exist_ok=True)
        with self._fichier(table).open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CHAMPS[table], extrasaction="ignore")
            w.writeheader()
            w.writerows(lignes)

    def lister(self, table):
        fichier = self._fichier(table)
        if not fichier.exists():
            return []
        with fichier.open(encoding="utf-8") as f:
            lecteur = csv.DictReader(f)
            entete = lecteur.fieldnames or []
            lignes = list(lecteur)
        if entete != CHAMPS[table]:            # ancien fichier : on complète les colonnes manquantes
            from suivi import nouvel_id
            for ligne in lignes:
                for champ in CHAMPS[table]:
                    if not ligne.get(champ):
                        ligne[champ] = nouvel_id() if champ == "id" else ""
            self._ecrire(table, lignes)
        return lignes

    def inserer(self, table, ligne):
        lignes = self.lister(table)
        lignes.append(ligne)
        self._ecrire(table, lignes)

    def modifier(self, table, id_, ligne):
        lignes = [ligne if l["id"] == id_ else l for l in self.lister(table)]
        self._ecrire(table, lignes)

    def supprimer(self, table, id_):
        self._ecrire(table, [l for l in self.lister(table) if l["id"] != id_])

    # --- documents ---
    def lister_documents(self, id_seance):
        d = self.documents / id_seance
        return sorted(p.name for p in d.iterdir() if p.is_file()) if d.exists() else []

    def deposer_document(self, id_seance, nom, contenu):
        d = self.documents / id_seance
        d.mkdir(parents=True, exist_ok=True)
        (d / nom).write_bytes(contenu)

    def ouvrir_document(self, id_seance, nom):
        return "octets", (self.documents / id_seance / nom).read_bytes()

    def supprimer_document(self, id_seance, nom):
        chemin = self.documents / id_seance / nom
        if chemin.exists():
            chemin.unlink()

    def supprimer_tous_documents(self, id_seance):
        for nom in self.lister_documents(id_seance):
            self.supprimer_document(id_seance, nom)
        d = self.documents / id_seance
        if d.exists():
            d.rmdir()


# ======================================================================
# Magasin Supabase (en ligne)
# ======================================================================

class MagasinSupabase:
    """Parle à Supabase avec de simples requêtes HTTP (bibliothèque requests)."""
    nom = "supabase"
    BUCKET = "documents"

    def __init__(self, url, cle):
        self.url = url.rstrip("/")
        self.entetes = {"apikey": cle}
        if cle.startswith("eyJ"):                 # ancienne clé « service_role » (format JWT)
            self.entetes["Authorization"] = f"Bearer {cle}"

    def _requete(self, methode, chemin, **kw):
        entetes = {**self.entetes, **kw.pop("headers", {})}
        r = requests.request(methode, f"{self.url}{chemin}", headers=entetes, timeout=20, **kw)
        if r.status_code >= 400:
            raise RuntimeError(f"Supabase a répondu {r.status_code} sur {methode} {chemin} : {r.text[:300]}")
        return r

    @staticmethod
    def _texte(ligne, table):
        """Supabase renvoie des nombres et des dates ; le reste du code attend du texte, comme avec les CSV."""
        return {c: ("" if ligne.get(c) is None else str(ligne.get(c))) for c in CHAMPS[table]}

    def lister(self, table):
        r = self._requete("GET", f"/rest/v1/{table}", params={"select": "*"})
        return [self._texte(l, table) for l in r.json()]

    def inserer(self, table, ligne):
        self._requete("POST", f"/rest/v1/{table}", json={c: ligne[c] for c in CHAMPS[table]},
                      headers={"Prefer": "return=minimal"})

    def modifier(self, table, id_, ligne):
        self._requete("PATCH", f"/rest/v1/{table}", params={"id": f"eq.{id_}"},
                      json={c: ligne[c] for c in CHAMPS[table] if c != "id"},
                      headers={"Prefer": "return=minimal"})

    def supprimer(self, table, id_):
        self._requete("DELETE", f"/rest/v1/{table}", params={"id": f"eq.{id_}"})

    # --- documents ---
    def lister_documents(self, id_seance):
        r = self._requete("POST", f"/storage/v1/object/list/{self.BUCKET}",
                          json={"prefix": f"{id_seance}/", "limit": 1000,
                                "sortBy": {"column": "name", "order": "asc"}})
        return [o["name"] for o in r.json() if o.get("id")]      # les « dossiers » n'ont pas d'id

    def deposer_document(self, id_seance, nom, contenu):
        type_mime = "application/pdf" if nom.lower().endswith(".pdf") else \
            "image/png" if nom.lower().endswith(".png") else "image/jpeg"
        self._requete("POST", f"/storage/v1/object/{self.BUCKET}/{id_seance}/{nom}", data=contenu,
                      headers={"Content-Type": type_mime, "x-upsert": "false"})

    def ouvrir_document(self, id_seance, nom):
        """Lien temporaire (1 h) pour ouvrir le document dans le navigateur."""
        r = self._requete("POST", f"/storage/v1/object/sign/{self.BUCKET}/{id_seance}/{nom}",
                          json={"expiresIn": 3600})
        lien = r.json().get("signedURL") or r.json().get("signedUrl")
        if not lien.startswith("http"):
            lien = f"{self.url}/storage/v1{lien}"
        return "lien", lien

    def supprimer_document(self, id_seance, nom):
        self._requete("DELETE", f"/storage/v1/object/{self.BUCKET}",
                      json={"prefixes": [f"{id_seance}/{nom}"]})

    def supprimer_tous_documents(self, id_seance):
        noms = self.lister_documents(id_seance)
        if noms:
            self._requete("DELETE", f"/storage/v1/object/{self.BUCKET}",
                          json={"prefixes": [f"{id_seance}/{n}" for n in noms]})


# ======================================================================
# Choix du magasin + petit cache (évite de rappeler Supabase 10 fois par affichage)
# ======================================================================

_magasin = None
_cache = {}
DUREE_CACHE = 30          # secondes


def magasin():
    global _magasin
    if _magasin is None:
        sb = lire_secrets().get("supabase")
        _magasin = MagasinSupabase(sb["url"], sb["cle"]) if sb else MagasinLocal()
    return _magasin


def en_cache(cle, fonction):
    maintenant = time.time()
    if not (cle in _cache and maintenant - _cache[cle][0] < DUREE_CACHE):
        _cache[cle] = (maintenant, fonction())
    return copy.deepcopy(_cache[cle][1])


def vider_cache():
    _cache.clear()
