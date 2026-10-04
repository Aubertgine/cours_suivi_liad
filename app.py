"""Interface du suivi des cours : python -m streamlit run app.py"""
import datetime as dt
import time

import streamlit as st

import auth
import revenu
import suivi as sv
from stockage import lire_secrets, magasin

PROFESSEUR = "Pierre-Antoine"
ELEVE = "Liad"
NIVEAU = "Seconde"
LYCEE = "Janson de Sailly"
TARIF_DEFAUT = 30.0
DEBUT_DEFAUT = dt.time(18, 15)
FIN_DEFAUT = dt.time(19, 45)


def vers_date(iso):
    return dt.date.fromisoformat(iso)


def vers_heure(texte):
    return dt.datetime.strptime(texte, "%H:%M").time()


def bandeau():
    st.markdown(f"""
<div class="entete">
  <div class="motif">∑ √ π</div>
  <div class="titre">Cours particulier de Mathématiques</div>
  <div class="personnes">
    <div><span>Professeur :</span> <b>{PROFESSEUR}</b></div>
    <div><span>Élève :</span> <b>{ELEVE} – {NIVEAU} – {LYCEE}</b></div>
  </div>
</div>
""", unsafe_allow_html=True)


st.set_page_config(page_title="Cours particulier maths Liad", layout="centered")

# ---------- Style ----------
st.markdown("""
<style>
.block-container {padding-top: 2.6rem; max-width: 880px;}

/* Bandeau */
.entete {position: relative; overflow: hidden; background: #FFFFFF; border: 1px solid #E3E7F0;
         border-radius: 20px; padding: 26px 30px; margin-bottom: 18px;
         box-shadow: 0 1px 2px rgba(30,36,51,.04), 0 8px 24px rgba(47,91,211,.06);}
.entete::before {content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 6px; background: #2F5BD3;}
.entete .motif {position: absolute; right: 26px; top: 50%; transform: translateY(-50%);
                font-size: 4.2rem; color: #2F5BD3; opacity: .08; font-weight: 800; letter-spacing: .1em;
                pointer-events: none; white-space: nowrap;}
.entete .titre {font-size: 2.05rem; font-weight: 800; color: #1E2433; line-height: 1.15; letter-spacing: -.01em;}
.entete .personnes {display: grid; gap: 4px; margin-top: 12px; font-size: 1.12rem;}
.entete .personnes span {color: #6B7389;}
.entete .personnes b {color: #1E2433; font-weight: 600;}

/* Onglets en pastilles */
[data-testid="stTabs"] [role="tablist"] {gap: 6px; background: #FFFFFF; border: 1px solid #E3E7F0;
        border-radius: 14px; padding: 6px; margin-bottom: 10px; box-shadow: 0 1px 2px rgba(30,36,51,.04);}
[data-testid="stTabs"] [role="tab"] {border-radius: 10px; padding: 8px 16px; height: auto; border: none;}
[data-testid="stTabs"] [role="tab"] p {font-size: 1rem; font-weight: 600; color: #4A5268;}
[data-testid="stTabs"] [role="tab"]:hover {background: #F6F7FB;}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {background: #EEF3FF;}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] p {color: #2F5BD3;}
[data-testid="stTabs"] .react-aria-SelectionIndicator,
div[data-baseweb="tab-highlight"], div[data-baseweb="tab-border"] {display: none;}

/* Cartes, formulaires, encadrés */
div[data-testid="stVerticalBlockBorderWrapper"], [class*="st-key-carte_"] {background: #FFFFFF; border-radius: 16px;
        box-shadow: 0 1px 2px rgba(30,36,51,.04);}
[class*="st-key-carte_"] div[data-testid="stExpander"] details {background: #F8F9FC; border-color: #EDF0F5;}
[data-testid="stTextInputRootElement"], div[data-baseweb="input"] {border: 1px solid #DDE2EC !important; border-radius: 10px !important;}
div[data-testid="stForm"] {background: #FFFFFF; border: 1px solid #E3E7F0; border-radius: 16px;}
div[data-testid="stExpander"] details {background: #FFFFFF; border: 1px solid #E3E7F0; border-radius: 16px;}
div[data-testid="stExpander"] summary p {font-weight: 600;}
div[data-testid="stMetric"] {background: #FFFFFF; border: 1px solid #E3E7F0; border-radius: 14px; padding: 12px 16px;}
div[data-testid="stMetricLabel"] p {color: #6B7389;}
[data-testid="stMarkdownContainer"] table {width: 100%; border-collapse: collapse; background: #FFFFFF;
                                           border-radius: 12px; overflow: hidden;}
[data-testid="stMarkdownContainer"] th {background: #F1F3F8; color: #4A5268; font-weight: 600;}
[data-testid="stMarkdownContainer"] th, [data-testid="stMarkdownContainer"] td {border: none; border-bottom: 1px solid #EDF0F5;}

/* Carte de séance (journal) */
.seance-date {font-size: 1.12rem; font-weight: 800; color: #1E2433;}
.seance-infos {display: flex; flex-wrap: wrap; gap: 8px; margin: 6px 0 2px;}
.puce {display: inline-block; background: #F1F3F8; color: #4A5268; border-radius: 999px;
       padding: 2px 11px; font-size: .86rem; font-weight: 600;}
.notion {margin-top: 10px; font-size: 1.02rem; color: #1E2433;}
.notion span {color: #6B7389;}
.notion.vide {color: #9AA1B3; font-style: italic;}

/* Somme due */
.solde {border-radius: 18px; padding: 22px 24px; margin: 4px 0 14px; border: 1px solid;}
.solde .libelle {font-size: .82rem; letter-spacing: .12em; text-transform: uppercase; font-weight: 700;}
.solde .montant {font-size: 3.1rem; font-weight: 800; line-height: 1.1; margin: 4px 0 6px;
                 font-variant-numeric: tabular-nums;}
.solde .contexte {font-size: .95rem; color: #4A5268;}
.solde.du      {background: #FFF4EC; border-color: #F6C9A8;} .solde.du .libelle, .solde.du .montant {color: #C2410C;}
.solde.regle   {background: #ECF8F0; border-color: #B5E0C2;} .solde.regle .libelle, .solde.regle .montant {color: #15803D;}
.solde.avance  {background: #EEF3FF; border-color: #BFD0FA;} .solde.avance .libelle, .solde.avance .montant {color: #1D4ED8;}
.pastille {display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: .82rem; font-weight: 600;}
.pastille.reglee     {background: #E3F5E8; color: #15803D;}
.pastille.partielle  {background: #FFEBDD; color: #C2410C;}
.pastille.attente    {background: #EEF0F4; color: #5B6377;}
.connecte {color: #6B7389; font-size: .92rem; padding-top: 6px;}
.carte-connexion {background: #FFFFFF; border: 1px solid #E3E7F0; border-radius: 16px; padding: 4px 6px;}
.felicitations {background: linear-gradient(160deg, #FFF8EF 0%, #FFFFFF 70%); border: 1px solid #F3DFC6;
                border-radius: 18px; padding: 22px 22px 20px; min-height: 230px;}
.felicitations .bravo {font-size: 1.25rem; font-weight: 800; color: #1E2433; margin-bottom: 8px;}
.felicitations .texte {font-size: 1.08rem; line-height: 1.55; color: #33394A; animation: apparition .6s ease-out;}
.felicitations .texte b {color: #C2410C;}
@keyframes apparition {from {opacity: 0; transform: translateY(6px);} to {opacity: 1; transform: none;}}
@media (prefers-reduced-motion: reduce) {.felicitations .texte {animation: none;}}
.revenu-total {font-size: .82rem; letter-spacing: .12em; text-transform: uppercase; font-weight: 700; color: #2F5BD3;}
.revenu-montant {font-size: 2.6rem; font-weight: 800; color: #1E2433; line-height: 1.1; margin: 2px 0 6px;
                 font-variant-numeric: tabular-nums;}
.titre-section {font-size: 1.1rem; font-weight: 800; color: #1E2433; margin: 18px 0 6px;}
</style>
""", unsafe_allow_html=True)


# ================= Connexion =================
utilisateurs = lire_secrets().get("utilisateurs", {})

if "compte" not in st.session_state:
    bandeau()
    if not utilisateurs:
        st.error("Aucun compte n'est configuré. Ajoute la section [utilisateurs] dans les secrets "
                 "(voir le README, étape « Créer les comptes »).")
        st.stop()
    _, centre, _ = st.columns([1, 2, 1])
    with centre:
        with st.form("connexion"):
            st.markdown("**Connexion**")
            identifiant = st.text_input("Identifiant")
            mot_de_passe = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Se connecter", type="primary", use_container_width=True):
                compte = auth.connecter(utilisateurs, identifiant, mot_de_passe)
                if compte:
                    st.session_state["compte"] = compte
                    st.rerun()
                time.sleep(1)                      # ralentit les essais au hasard
                st.error("Identifiant ou mot de passe incorrect.")
    st.stop()

compte = st.session_state["compte"]
est_prof = compte["role"] == "prof"

# ================= Barre du haut + bandeau =================
c_info, c_bouton = st.columns([5, 1.3], vertical_alignment="center")
c_info.markdown(f'<div class="connecte">Connecté : <b>{compte["nom"]}</b>'
                + (" · mode local" if magasin().nom == "local" else "") + "</div>", unsafe_allow_html=True)
if c_bouton.button("Se déconnecter", use_container_width=True):
    del st.session_state["compte"]
    st.rerun()
bandeau()

seances = sv.lire_seances()
versements = sv.lire_versements()
solde = sv.solde()
statuts = sv.statut_seances()

# ================= Onglets (selon le compte) =================
if est_prof:
    tab_journal, tab_paiements, tab_historique, tab_modifier, tab_revenu = st.tabs(
        ["Journal des séances", "Paiements", "Historique", "Modifier ou supprimer", "Revenu"])
else:
    tab_journal, tab_paiements = st.tabs(["Journal des séances", "Paiements"])

# ---------- Journal des séances ----------
with tab_journal:
    if est_prof:
        with st.expander("Ajouter une séance", expanded=not seances):
            with st.form("nouvelle_seance", clear_on_submit=True, border=False):
                a, b, c, d = st.columns(4)
                date = a.date_input("Date", value=dt.date.today(), format="DD/MM/YYYY")
                debut = b.time_input("Début", value=DEBUT_DEFAUT, step=300)
                fin = c.time_input("Fin", value=FIN_DEFAUT, step=300)
                tarif = d.number_input("Tarif horaire (€)", min_value=0.0, value=TARIF_DEFAUT, step=1.0)
                notion = st.text_input("Notion abordée", placeholder="ex. : Factorisation, identités remarquables")
                if st.form_submit_button("Ajouter la séance", type="primary"):
                    if fin <= debut:
                        st.error("L'heure de fin doit être après l'heure de début.")
                    else:
                        sv.ajouter_seance(date.isoformat(), debut.strftime("%H:%M"), fin.strftime("%H:%M"),
                                          tarif, notion.strip())
                        st.rerun()

    if not seances:
        st.info("Aucune séance pour l'instant.")
    for s in reversed(seances):                                   # la plus récente en haut
        with st.container(border=True, key=f"carte_{s['id']}"):
            documents = sv.lister_documents(s["id"])
            puces = [f'{s["debut"]} – {s["fin"]}', sv.duree_texte(s)]
            if documents:
                puces.append(f"{len(documents)} document" + ("s" if len(documents) > 1 else ""))
            if s["notion"]:
                notion_html = f'<div class="notion"><span>Notion :</span> {s["notion"]}</div>'
            elif est_prof:
                notion_html = '<div class="notion vide">Notion non renseignée – à compléter dans « Modifier ou supprimer »</div>'
            else:
                notion_html = '<div class="notion vide">Notion non renseignée</div>'
            st.markdown(f'<div class="seance-date">{sv.date_longue(s["date"])}</div>'
                        f'<div class="seance-infos">{"".join(f"<span class=puce>{p}</span>" for p in puces)}</div>'
                        f'{notion_html}', unsafe_allow_html=True)

            for nom in documents:
                est_pdf = nom.lower().endswith(".pdf")
                colonnes = st.columns([6, 2, 2] if est_prof else [8, 2], vertical_alignment="center")
                colonnes[0].write(("📄 " if est_pdf else "🖼️ ") + nom)
                genre, valeur = sv.ouvrir_document(s["id"], nom)
                if genre == "lien":
                    colonnes[1].link_button("Ouvrir", valeur, use_container_width=True)
                else:
                    colonnes[1].download_button(
                        "Ouvrir", data=valeur, file_name=nom, use_container_width=True,
                        mime="application/pdf" if est_pdf else "image/" + nom.rsplit(".", 1)[-1].lower().replace("jpg", "jpeg"),
                        key=f"ouvrir_{s['id']}_{nom}")
                if est_prof:
                    with colonnes[2].popover("Supprimer", use_container_width=True):
                        st.write(f"Supprimer « {nom} » ?")
                        if st.button("Oui, supprimer", key=f"suppr_{s['id']}_{nom}", type="primary"):
                            sv.supprimer_document(s["id"], nom)
                            st.rerun()

            if est_prof:
                with st.expander("Joindre des documents"):
                    with st.form(f"docs_{s['id']}", clear_on_submit=True, border=False):
                        fichiers = st.file_uploader("PDF, JPG ou PNG", type=sv.TYPES_DOCUMENTS,
                                                    accept_multiple_files=True, key=f"upload_{s['id']}")
                        if st.form_submit_button("Joindre", type="primary"):
                            for f in fichiers or []:
                                sv.ajouter_document(s["id"], f.name, f.getvalue())
                            if fichiers:
                                st.rerun()

# ---------- Paiements ----------
with tab_paiements:
    en_attente = sum(1 for _, statut, _ in statuts if statut != "réglée")
    if versements:
        info_virement = f"dernier virement le {sv.date_fr(versements[-1]['date'])}"
    else:
        info_virement = "aucun virement reçu pour l'instant"
    if solde > 0:
        classe, libelle, valeur = "du", "Reste à régler", sv.euros(solde)
        pluriel = "s" if en_attente > 1 else ""
        contexte = f"{en_attente} séance{pluriel} non réglée{pluriel} · {info_virement}"
    elif solde < 0:
        classe, libelle, valeur = "avance", "Avance reçue", sv.euros(-solde)
        contexte = f"Les prochaines séances sont déjà couvertes · {info_virement}"
    else:
        classe, libelle, valeur = "regle", "Tout est réglé", sv.euros(0)
        contexte = info_virement.capitalize() if seances else "Aucune séance enregistrée pour l'instant"
    st.markdown(f'<div class="solde {classe}"><div class="libelle">{libelle}</div>'
                f'<div class="montant">{valeur}</div><div class="contexte">{contexte}</div></div>',
                unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Heures données", f"{sum(sv.duree_heures(s) for s in seances):.1f} h".replace(".", ","))
    c2.metric("Séances", len(seances))
    c3.metric("Total reçu", sv.euros(sv.total_versements()))

    if est_prof:
        st.write("")
        with st.expander("Ajouter un virement reçu"):
            with st.form("nouveau_versement", clear_on_submit=True, border=False):
                a, b = st.columns(2)
                date_v = a.date_input("Date du virement", value=dt.date.today(), format="DD/MM/YYYY")
                montant_v = b.number_input("Montant reçu (€)", min_value=0.0, value=0.0, step=5.0)
                note_v = st.text_input("Note (facultatif)", placeholder="ex. : virement des parents pour septembre")
                if st.form_submit_button("Ajouter le virement", type="primary"):
                    if montant_v <= 0:
                        st.error("Le montant doit être supérieur à 0.")
                    else:
                        sv.ajouter_versement(date_v.isoformat(), montant_v, note_v.strip())
                        st.rerun()

    st.markdown('<div class="titre-section">Statut des séances</div>', unsafe_allow_html=True)
    if not seances:
        st.caption("Aucune séance pour l'instant.")
    else:
        lignes = ["| Date | Horaire | Durée | Montant | Statut |", "|---|---|---|---:|---|"]
        for s, statut, reste in reversed(statuts):
            if statut == "réglée":
                pastille = '<span class="pastille reglee">réglée</span>'
            elif statut == "partielle":
                pastille = f'<span class="pastille partielle">partielle · {sv.euros(reste)} restants</span>'
            else:
                pastille = '<span class="pastille attente">en attente</span>'
            lignes.append(f"| {sv.date_fr(s['date'])} | {s['debut']} – {s['fin']} | {sv.duree_texte(s)} "
                          f"| {sv.euros(sv.montant(s))} | {pastille} |")
        st.markdown("\n".join(lignes), unsafe_allow_html=True)

# ---------- Les onglets suivants n'existent que pour le professeur ----------
if not est_prof:
    st.stop()

# ---------- Historique ----------
with tab_historique:
    evenements = sv.historique()
    if not evenements:
        st.info("L'historique apparaîtra ici dès la première séance ou le premier virement.")
    else:
        lignes = ["| Date | Opération | Montant | Solde |", "|---|---|---:|---:|"]
        for e in reversed(evenements):
            signe = "+" if e["montant"] > 0 else "−"
            lignes.append(f"| {sv.date_fr(e['date'])} | {e['libelle']} "
                          f"| {signe} {sv.euros(abs(e['montant']))} | {sv.euros(e['solde'])} |")
        st.markdown("\n".join(lignes))
        st.caption("Solde positif : on te doit de l'argent. Solde négatif : avance reçue.")

# ---------- Modifier ou supprimer ----------
with tab_modifier:
    genre = st.radio("Élément", ["Une séance", "Un virement"], horizontal=True, label_visibility="collapsed")

    if genre == "Une séance":
        if not seances:
            st.caption("Aucune séance enregistrée.")
        else:
            choix = st.selectbox(
                "Séance", list(reversed(seances)),
                format_func=lambda s: f"{sv.date_fr(s['date'])} · {s['debut']} – {s['fin']} · "
                                      f"{sv.euros(sv.montant(s))}" + (f" · {s['notion']}" if s["notion"] else ""))
            id_ = choix["id"]
            with st.form(f"modif_seance_{id_}"):
                a, b, c, d = st.columns(4)
                date_m = a.date_input("Date", value=vers_date(choix["date"]), format="DD/MM/YYYY")
                debut_m = b.time_input("Début", value=vers_heure(choix["debut"]), step=300)
                fin_m = c.time_input("Fin", value=vers_heure(choix["fin"]), step=300)
                tarif_m = d.number_input("Tarif horaire (€)", min_value=0.0,
                                         value=float(choix["tarif_horaire"]), step=1.0)
                notion_m = st.text_input("Notion abordée", value=choix["notion"])
                if st.form_submit_button("Enregistrer les modifications"):
                    if fin_m <= debut_m:
                        st.error("L'heure de fin doit être après l'heure de début.")
                    else:
                        sv.modifier_seance(id_, date_m.isoformat(), debut_m.strftime("%H:%M"),
                                           fin_m.strftime("%H:%M"), tarif_m, notion_m.strip())
                        st.rerun()
            nb_docs = len(sv.lister_documents(id_))
            texte = "Je confirme la suppression de cette séance"
            if nb_docs:
                texte += f" et de ses {nb_docs} document(s) joint(s)"
            confirmer = st.checkbox(texte, key=f"conf_s_{id_}")
            if st.button("Supprimer la séance", disabled=not confirmer):
                sv.supprimer_seance(id_)
                st.rerun()
    else:
        if not versements:
            st.caption("Aucun virement enregistré.")
        else:
            choix = st.selectbox(
                "Virement", list(reversed(versements)),
                format_func=lambda v: f"{sv.date_fr(v['date'])} · {sv.euros(float(v['montant']))}"
                                      + (f" · {v['note']}" if v["note"] else ""))
            id_ = choix["id"]
            with st.form(f"modif_versement_{id_}"):
                a, b = st.columns(2)
                date_m = a.date_input("Date du virement", value=vers_date(choix["date"]), format="DD/MM/YYYY")
                montant_m = b.number_input("Montant reçu (€)", min_value=0.0, value=float(choix["montant"]), step=5.0)
                note_m = st.text_input("Note (facultatif)", value=choix["note"])
                if st.form_submit_button("Enregistrer les modifications"):
                    if montant_m <= 0:
                        st.error("Le montant doit être supérieur à 0.")
                    else:
                        sv.modifier_versement(id_, date_m.isoformat(), montant_m, note_m.strip())
                        st.rerun()
            confirmer = st.checkbox("Je confirme la suppression de ce virement", key=f"conf_v_{id_}")
            if st.button("Supprimer le virement", disabled=not confirmer):
                sv.supprimer_versement(id_)
                st.rerun()


# ---------- Revenu ----------
@st.fragment(run_every=7)
def message_felicitations(total):
    """Ce petit cadre se rafraîchit tout seul toutes les 7 secondes (pas le reste de la page)."""
    dernier = st.session_state.get("dernier_produit")
    st.session_state["dernier_produit"], texte = revenu.message_aleatoire(total, dernier)
    st.markdown(f'<div class="felicitations"><div class="bravo">Bravo, {PROFESSEUR} ! 🎉</div>'
                f'<div class="texte">{texte}</div></div>', unsafe_allow_html=True)


with tab_revenu:
    total = sv.total_seances()
    if not seances:
        st.info("Le graphe apparaîtra dès la première séance.")
    else:
        gauche, droite = st.columns([3, 2], gap="medium")
        with gauche:
            st.markdown(f'<div class="revenu-total">Revenu généré</div>'
                        f'<div class="revenu-montant">{sv.euros(total)}</div>'
                        + revenu.legende_html(), unsafe_allow_html=True)
            st.markdown(revenu.graphe_svg(sv.revenu_cumule()), unsafe_allow_html=True)
            st.caption("Cumul séance après séance. Survole un point pour voir le détail.")
        with droite:
            message_felicitations(total)
