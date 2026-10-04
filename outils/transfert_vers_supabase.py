"""Copie une seule fois les données locales (dossier donnees/) vers Supabase.

Pré-requis : .streamlit/secrets.toml contient la section [supabase].
Utilisation (dans le terminal, dossier du projet) :
    python outils/transfert_vers_supabase.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from stockage import MagasinLocal, MagasinSupabase, lire_secrets  # noqa: E402

sb = lire_secrets().get("supabase")
if not sb:
    sys.exit("Ajoute d'abord la section [supabase] dans .streamlit/secrets.toml.")

local = MagasinLocal()
enligne = MagasinSupabase(sb["url"], sb["cle"])

for table in ("seances", "versements"):
    deja = {l["id"] for l in enligne.lister(table)}
    lignes = local.lister(table)
    nouvelles = [l for l in lignes if l["id"] not in deja]
    for l in nouvelles:
        enligne.inserer(table, l)
    print(f"{table} : {len(nouvelles)} ajoutée(s), {len(lignes) - len(nouvelles)} déjà présente(s).")

nb = 0
for s in local.lister("seances"):
    deja = set(enligne.lister_documents(s["id"]))
    for nom in local.lister_documents(s["id"]):
        if nom not in deja:
            _, contenu = local.ouvrir_document(s["id"], nom)
            enligne.deposer_document(s["id"], nom, contenu)
            nb += 1
print(f"documents : {nb} envoyé(s).")
print("Terminé. Tes fichiers locaux n'ont pas été modifiés.")
