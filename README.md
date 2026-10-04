# Cours particulier de Mathématiques – suivi

Application Streamlit : journal des séances (notions, documents), paiements, historique,
revenu. Deux comptes : le professeur (tout) et l'élève (journal + paiements, en lecture seule).

## Fichiers

- `app.py` : l'interface (pages, onglets, formulaires).
- `suivi.py` : les calculs (solde, statut des séances, historique, revenu cumulé).
- `stockage.py` : où sont rangées les données (en local ou sur Supabase).
- `auth.py` : connexion par identifiant / mot de passe.
- `revenu.py` : graphe du revenu et messages de félicitations.
- `outils/` : scripts à lancer une seule fois (mots de passe, création de la base, transfert).
- `.streamlit/config.toml` : couleurs ; `.streamlit/secrets.toml` : clés et comptes (jamais sur GitHub).

## Lancer en local

    .venv\Scripts\Activate.ps1
    python -m pip install -r requirements.txt
    python -m streamlit run app.py

Sans section `[supabase]` dans les secrets, les données restent dans `donnees/` sur le PC.
