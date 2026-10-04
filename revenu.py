"""Onglet Revenu : graphe du revenu cumulé et messages de félicitations."""
import math
import random
from datetime import date as Date

import suivi as sv

BLEU = "#2F5BD3"      # déjà reçu
ORANGE = "#E0782F"    # en attente
ENCRE = "#1E2433"
GRIS = "#6B7389"
GRILLE = "#E8EBF2"

# (prix approximatif en €, singulier, pluriel, chute)
PRODUITS = [
    (4.50, "cappuccino", "cappuccinos",
     "Dans un café où le barista dessine un π dans la mousse, si on lui demande gentiment."),
    (2.80, "bretzel", "bretzels",
     "De quoi tenir tout l'Oktoberfest sans jamais faiblir."),
    (12.00, "paire de chaussettes à motif π", "paires de chaussettes à motif π",
     "Soit environ 3,14 paires par pied. C'est rigoureux."),
    (2.00, "pot de cornichons", "pots de cornichons",
     "Personne n'a besoin d'autant de cornichons. Mais tu pourrais."),
    (7.50, "partie de bowling", "parties de bowling",
     "Idéal pour réviser les trajectoires en conditions réelles."),
    (15.00, "heure de kayak", "heures de kayak",
     "Parfait pour méditer sur les vecteurs vitesse au fil de l'eau."),
    (1.30, "croissant", "croissants",
     "Un par identité remarquable démontrée, et il en reste."),
    (6.00, "petit cactus", "petits cactus",
     "Les seuls élèves qui ne demandent jamais « ça sert à quoi dans la vie ? »."),
    (10.00, "Rubik's Cube", "Rubik's Cubes",
     "43 trillions de combinaisons chacun : de quoi occuper les week-ends."),
    (3.00, "canard en plastique", "canards en plastique",
     "Pour expliquer tes calculs à quelqu'un qui écoute vraiment."),
    (8.00, "tour de grande roue", "tours de grande roue",
     "Le cercle trigonométrique, version fête foraine."),
    (5.00, "gaufre au sucre", "gaufres au sucre",
     "Parce qu'un quadrillage parfait, ça se mange aussi."),
    (25.00, "balade avec un lama", "balades avec un lama",
     "Un animal qui, comme une bonne démonstration, ne se presse jamais."),
    (9.00, "kebab sauce samouraï", "kebabs sauce samouraï",
     "Le carburant officiel des profs particuliers."),
    (0.10, "trombone", "trombones",
     "De quoi relier toutes les copies de seconde de France. Presque."),
]


def message_aleatoire(total, dernier=None):
    """Choisit un produit au hasard (différent du précédent) et compose le message."""
    choix = [i for i in range(len(PRODUITS)) if i != dernier]
    i = random.choice(choix)
    prix, sing, plur, chute = PRODUITS[i]
    n = math.floor(total / prix)
    if n == 0:
        texte = f"Pas encore de quoi t'offrir un(e) {sing}… mais chaque séance te rapproche du but."
    else:
        produit = sing if n == 1 else plur
        nombre = f"{n:,}".replace(",", " ")
        texte = f"Avec cette somme, tu pourrais t'offrir <b>{nombre} {produit}</b>. {chute}"
    return i, texte


# ---------- Graphe : aires empilées du revenu cumulé ----------

def _graduations(maximum):
    """Graduations « rondes » pour l'axe des euros (ex. 0, 100, 200, 300)."""
    if maximum <= 0:
        return [0, 10]
    brut = maximum / 4
    puissance = 10 ** math.floor(math.log10(brut))
    pas = min((p * puissance for p in (1, 2, 2.5, 5, 10) if p * puissance >= brut), default=brut)
    return [round(pas * k, 2) for k in range(0, math.ceil(maximum / pas) + 1)]


def graphe_svg(points):
    """points = [(date_iso, cumul_recu, cumul_attente), ...] -> SVG (chaîne de caractères)."""
    L, H = 520, 300
    g, d, h, b = 54, 96, 16, 30                # marges : gauche, droite (place des étiquettes), haut, bas
    reels = [Date.fromisoformat(p[0]).toordinal() for p in points]
    # Série complète : on part de 0 la veille de la 1re séance, et on prolonge jusqu'à aujourd'hui.
    jours = [reels[0] - 1] + reels
    recus = [0.0] + [r for _, r, _ in points]
    totaux = [0.0] + [r + a for _, r, a in points]
    aujourdhui = Date.today().toordinal()
    if aujourdhui > reels[-1]:
        jours.append(aujourdhui)
        recus.append(recus[-1])
        totaux.append(totaux[-1])
    j0, j1 = jours[0], jours[-1]
    ticks = _graduations(max(totaux))
    ymax = ticks[-1]

    def X(j):
        return g + (j - j0) / (j1 - j0) * (L - g - d)

    def Y(v):
        return h + (1 - v / ymax) * (H - h - b)

    # Escaliers : le cumul reste plat entre deux séances, puis monte d'un coup.
    def escalier(valeurs):
        pts = []
        for k, (j, v) in enumerate(zip(jours, valeurs)):
            if k > 0:
                pts.append((X(j), Y(valeurs[k - 1])))
            pts.append((X(j), Y(v)))
        return pts

    haut_recu = escalier(recus)
    haut_total = escalier(totaux)
    base = [(x, Y(0)) for x, _ in reversed(haut_recu)]

    def chemin(pts):
        return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"

    svg = [f'<svg viewBox="0 0 {L} {H}" width="100%" role="img" '
           f'aria-label="Revenu cumulé : déjà reçu et en attente" style="font-family:inherit">']
    # Grille et axe des euros
    for t in ticks:
        y = Y(t)
        svg.append(f'<line x1="{g}" x2="{L - d}" y1="{y:.1f}" y2="{y:.1f}" stroke="{GRILLE}" stroke-width="1"/>')
        svg.append(f'<text x="{g - 8}" y="{y + 4:.1f}" text-anchor="end" font-size="13" fill="{GRIS}">'
                   f'{int(t) if t == int(t) else t} €</text>')
    # Aires : reçu (en bas) puis en attente (empilé au-dessus), séparées d'un fin liseré blanc
    svg.append(f'<path d="{chemin(haut_recu + base)}" fill="{BLEU}" fill-opacity=".88"/>')
    svg.append(f'<path d="{chemin(haut_total + list(reversed(haut_recu)))}" fill="{ORANGE}" fill-opacity=".85"/>')
    svg.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in haut_recu)}" fill="none" '
               f'stroke="#FFFFFF" stroke-width="2"/>')
    svg.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in haut_total)}" fill="none" '
               f'stroke="{ENCRE}" stroke-opacity=".55" stroke-width="2"/>')
    # Points (avec infobulle au survol) à chaque séance
    for (dt, r, a), j in zip(points, reels):
        x, y = X(j), Y(r + a)
        svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="transparent">'
                   f'<title>{sv.date_fr(dt)} · total {sv.euros(r + a)} · reçu {sv.euros(r)} · '
                   f'en attente {sv.euros(a)}</title></circle>')
        svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#FFFFFF" stroke="{ENCRE}" '
                   f'stroke-width="2" pointer-events="none"/>')
    # Dates : première et dernière séance (+ une au milieu s'il y en a assez)
    reperes = {0, len(points) - 1}
    if len(points) >= 5:
        reperes.add(len(points) // 2)
    for k in sorted(reperes):
        ancre = "start" if k == 0 else "end" if k == len(points) - 1 else "middle"
        svg.append(f'<text x="{X(reels[k]):.1f}" y="{H - 10}" text-anchor="{ancre}" font-size="13" '
                   f'fill="{GRIS}">{sv.date_courte(points[k][0])}</text>')
    # Étiquettes directes au bout des aires
    _, r_fin, a_fin = points[-1]
    x_fin = X(jours[-1]) + 10
    y_recu = Y(r_fin / 2) if r_fin else None
    y_att = Y(r_fin + a_fin / 2) if a_fin else None
    if y_recu and y_att and abs(y_recu - y_att) < 30:      # évite que les deux étiquettes se chevauchent
        y_att = y_recu - 30
    if y_recu:
        svg.append(f'<text x="{x_fin:.1f}" y="{y_recu:.1f}" font-size="14" fill="{ENCRE}">'
                   f'<tspan font-weight="700">Reçu</tspan><tspan x="{x_fin:.1f}" dy="17" fill="{GRIS}">'
                   f'{sv.euros(r_fin)}</tspan></text>')
    if y_att:
        svg.append(f'<text x="{x_fin:.1f}" y="{y_att:.1f}" font-size="14" fill="{ENCRE}">'
                   f'<tspan font-weight="700">En attente</tspan><tspan x="{x_fin:.1f}" dy="17" fill="{GRIS}">'
                   f'{sv.euros(a_fin)}</tspan></text>')
    svg.append("</svg>")
    return "".join(svg)


def legende_html():
    pastille = '<span style="display:inline-block;width:12px;height:12px;border-radius:3px;background:{};' \
               'margin-right:6px;vertical-align:-1px"></span>'
    return (f'<div style="display:flex;gap:18px;font-size:.9rem;color:{GRIS};margin:2px 0 4px">'
            f'<span>{pastille.format(BLEU)}Déjà reçu</span>'
            f'<span>{pastille.format(ORANGE)}En attente</span></div>')
