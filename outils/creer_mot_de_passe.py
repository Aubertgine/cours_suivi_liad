"""Génère l'empreinte d'un mot de passe, à coller dans les secrets.

Utilisation (dans le terminal, dossier du projet) :
    python outils/creer_mot_de_passe.py
Le mot de passe tapé n'apparaît pas à l'écran : c'est normal.
"""
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import auth  # noqa: E402

mdp = getpass.getpass("Mot de passe : ")
if len(mdp) < 8:
    sys.exit("Choisis au moins 8 caractères.")
if getpass.getpass("Retape-le : ") != mdp:
    sys.exit("Les deux mots de passe ne sont pas identiques.")
print("\nCopie cette ligne dans les secrets :\n")
print(f'mot_de_passe = "{auth.empreinte(mdp)}"')
