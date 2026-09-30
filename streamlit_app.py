"""Tableau de bord Rikolto RDC · Café & Cacao 2019-2025 (Streamlit Community Cloud).

Données : agrégats café par campagne × coopérative et 88 ménages cacao sans identifiant (posit/donnees/),
écrits par scripts/exports/build_posit_data.py.
"""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Rikolto Café & Cacao", page_icon=":material/agriculture:", layout="wide")

DONNEES = Path(__file__).parent / "posit" / "donnees"
C = {"vert": "#1F5C4A", "cafe": "#8C5A3C", "sable": "#DDB690", "ambre": "#B07A12", "ardoise": "#4A6FA5",
     "rouge": "#B23A48", "sauge": "#9DBFAE", "gris": "#DCE1DA"}
OPS_HIST = ("CKK", "COOKKANZ")
MIN_N1 = 30  # en dessous, la coopérative est considérée comme nouvelle : pas de taux de rétention
GRAVITES = ["Critique", "Élevée", "Moyenne", "Faible"]
SOURCES = {"Rev_Cacao": "Cacao", "Rev_Agroforesterie": "Agroforesterie", "Rev_Hors_Ferme": "Activités hors ferme",
           "Rev_Transferts": "Transferts et autres", "Rev_Elevage": "Élevage", "Rev_Cafe": "Café",
           "Rev_Autres_Cultures": "Autres cultures vivrières"}


@st.cache_data
def charger():
    lire = lambda f: pd.read_csv(DONNEES / f, encoding="utf-8")
    params = lire("parametres.csv").set_index("parametre")["valeur"]
    return {"cafe": lire("cafe_campagne_op.csv"), "uniques": lire("personnes_uniques.csv").astype({"annee": str}),
            "menages": lire("menages_cacao.csv"), "okapi": lire("okapi_sections.csv"), "qualite": lire("qualite_controles.csv"),
            "seuil": float(params.filter(like="Seuil revenu vital").iloc[0]),
            "pauvrete": float(params.filter(like="pauvret").iloc[0]),
            "fideles7": int(lire("divers.csv").iloc[0, 1])}


D = charger()
CAFE, MEN, QUAL = D["cafe"], D["menages"], D["qualite"]
ANNEES = sorted(CAFE.annee.unique())
OPS = sorted(CAFE.op.unique())
SECTIONS = sorted(MEN.Section.unique())


# ---------------------------------------------------------------- formats (français)
def fr0(x):
    return "–" if pd.isna(x) else f"{round(x):,}".replace(",", " ")


def fr1(x):
    return "–" if pd.isna(x) else f"{x:.1f}".replace(".", ",")


def fr2(x):
    return "–" if pd.isna(x) else f"{x:.2f}".replace(".", ",")


def pct(x, d=1):
    return "–" if x is None or pd.isna(x) else f"{100 * x:.{d}f}".replace(".", ",") + " %"


def fig_base(fig, height=320, **kw):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", legend=dict(orientation="h", y=1.08, x=0),
                      font=dict(family="IBM Plex Sans, sans-serif"), separators=", ", **kw)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(128,128,128,0.18)")
    return fig


def graphique(fig):
    st.plotly_chart(fig, config={"displayModeBar": False})


# ---------------------------------------------------------------- calculs café
def filtre_cafe(annee, op):
    ans = ANNEES if annee == "Toutes" else [int(annee)]
    ops = OPS if op == "Toutes" else [op]
    return CAFE[CAFE.annee.isin(ans) & CAFE.op.isin(ops)]


def somme(df):
    return df.select_dtypes("number").drop(columns=["annee"], errors="ignore").sum()


def retention(annee, op):
    df = filtre_cafe(annee, op)
    if df.empty:
        return None
    y = df.annee.max() if annee == "Toutes" else int(annee)
    cur, prev = somme(filtre_cafe(str(y), op)), somme(filtre_cafe(str(y - 1), op))
    return None if prev["n"] < MIN_N1 else cur["present_n1"] / prev["n"]


def personnes(annee, op):
    u = D["uniques"]
    r = u[(u.annee == str(annee)) & (u.op == op)]
    return r.personnes.iloc[0] if len(r) else None


# ---------------------------------------------------------------- calculs cacao
def stats_cacao(m):
    sous = m[m.Revenu_Net_Total_USD < m.Seuil_LI_Ajuste_USD]
    return {"n": len(m), "rev": m.Revenu_Net_Total_USD.median(), "ref": m.Atteint_LI_Menage_Ref.mean(),
            "adj": m.Atteint_LI_Ajuste_Taille.mean(),
            "ecart": (sous.Seuil_LI_Ajuste_USD - sous.Revenu_Net_Total_USD).median() if len(sous) else None,
            "pcj": m.Revenu_par_personne_jour.median(), "sous215": (m.Revenu_par_personne_jour < D["pauvrete"]).mean(),
            "solde": (m.Solde_Revenu_Depenses_USD < 0).mean(), "taille": m.Taille_Menage.mean(),
            "part_cacao": m.Rev_Cacao.sum() / m.Revenu_Net_Total_USD.sum(), "femmes": int((m.Sexe == "Femme").sum())}


def kpis(items):
    with st.container(horizontal=True):
        for label, valeur, aide in items:
            st.metric(label, valeur, help=aide, border=True)


def filtres_cafe(cle):
    with st.sidebar:
        st.subheader("Filtres")
        annee = st.selectbox("Campagne", ["Toutes"] + [str(a) for a in ANNEES], key=f"{cle}_annee")
        op = st.selectbox("Coopérative", ["Toutes"] + OPS, key=f"{cle}_op")
        st.caption("Les graphiques par campagne suivent le filtre Coopérative.")
    return annee, op


# ================================================================ pages
def page_synthese():
    st.title("Synthèse pour la direction")
    st.caption(f"Chiffres clés café (campagne 2025) et cacao (enquête revenu vital, mars 2024). "
               f"Seuil Anker RDC rurale 2025 : {fr0(D['seuil'])} USD/an pour un ménage de 6 personnes.")
    s, m = somme(filtre_cafe("2025", "Toutes")), stats_cacao(MEN)
    kpis([("Producteurs café 2025", fr0(s.n), None), ("Femmes", pct(s.femmes / s.n), None),
          ("Jeunes 15-35 ans", pct(s.jeunes / s.n), "Rapportés à l'ensemble des producteurs"),
          ("Superficie café (ha)", fr0(s.sup), None), ("Certifiés conformes", pct(s.conforme / s.n), None)])
    kpis([("Ménages cacao enquêtés", str(m["n"]), None), ("Revenu net médian (USD/an)", fr0(m["rev"]), f"Seuil : {fr0(D['seuil'])} USD/an"),
          ("Au-dessus du seuil (réf.)", pct(m["ref"], 0), "Ménage de référence de 6 personnes"),
          ("Au-dessus du seuil ajusté", pct(m["adj"], 0), f"Taille réelle moyenne : {fr1(m['taille'])} personnes"),
          ("Contrôles qualité critiques", f"{(QUAL.Gravite == 'Critique').sum()} / {len(QUAL)}", None)])

    col1, col2 = st.columns(2)
    with col1, st.container(border=True):
        st.markdown("**Producteurs café enregistrés par campagne**")
        st.caption("Doublement en 2024-2025 lié à l'intégration de COOPADE puis COOKURU")
        g = CAFE.assign(groupe=CAFE.op.isin(OPS_HIST).map({True: "CKK et COOKKANZ (historiques)", False: "COOPADE et COOKURU (nouvelles)"}))
        g = g.groupby(["annee", "groupe"], as_index=False).n.sum()
        fig = go.Figure()
        for grp, coul in (("CKK et COOKKANZ (historiques)", C["cafe"]), ("COOPADE et COOKURU (nouvelles)", C["sable"])):
            d = g[g.groupe == grp]
            fig.add_bar(x=d.annee.astype(str), y=d.n, name=grp, marker_color=coul, hovertemplate="%{x} : %{y:,}<extra></extra>")
        tot = g.groupby("annee").n.sum()
        fig.add_scatter(x=tot.index.astype(str), y=tot.values, mode="text", text=[fr0(v) for v in tot.values],
                        textposition="top center", showlegend=False, hoverinfo="skip")
        graphique(fig_base(fig, barmode="stack"))
    with col2, st.container(border=True):
        st.markdown("**Ménages cacao atteignant le revenu vital, par section**")
        st.caption("Seuil de référence et seuil ajusté à la taille réelle du ménage")
        t = MEN.groupby("Section")[["Atteint_LI_Menage_Ref", "Atteint_LI_Ajuste_Taille"]].mean().sort_values("Atteint_LI_Menage_Ref")
        fig = go.Figure()
        fig.add_bar(y=t.index, x=t.Atteint_LI_Menage_Ref, orientation="h", name="Seuil de référence", marker_color=C["sauge"],
                    text=[pct(v, 0) for v in t.Atteint_LI_Menage_Ref], textposition="outside", hoverinfo="skip")
        fig.add_bar(y=t.index, x=t.Atteint_LI_Ajuste_Taille, orientation="h", name="Seuil ajusté à la taille", marker_color=C["vert"],
                    text=[pct(v, 0) for v in t.Atteint_LI_Ajuste_Taille], textposition="outside", hoverinfo="skip")
        graphique(fig_base(fig, barmode="group", xaxis=dict(tickformat=".0%", range=[0, 1])))

    with st.container(border=True):
        st.markdown("**Messages clés**")
        st.markdown(
            f"1. **Couverture** : {fr0(s.n)} producteurs café en 2025 (×3,2 depuis 2019), {pct(s.femmes / s.n)} de femmes et "
            f"{pct(s.jeunes / s.n)} de jeunes. Les coopératives historiques progressent de +68 %.\n"
            f"2. **Revenu cacao** : revenu net médian de {fr0(m['rev'])} USD/an ; {pct(m['ref'], 0)} des ménages dépassent le seuil de "
            f"référence, {pct(m['adj'], 0)} seulement une fois le seuil ajusté à la taille des ménages.\n"
            f"3. **Vulnérabilité** : {pct(m['part_cacao'], 0)} du revenu vient du cacao et {pct(m['sous215'], 0)} des ménages vivent "
            f"avec moins de 2,15 USD par personne et par jour.\n"
            f"4. :red[**Données** : production, chiffre d'affaires et marge café sont calculés par paramètres fixes et ne mesurent pas l'impact.]")


def page_beneficiaires():
    st.title("Café : bénéficiaires et inclusion")
    annee, op = filtres_cafe("b")
    s, r = somme(filtre_cafe(annee, op)), retention(annee, op)
    kpis([("Personnes", fr0(personnes(annee, op)), f"{fr0(s.n)} inscriptions (un producteur × une campagne)"),
          ("Nouveaux producteurs", fr0(s.nouveaux), None),
          ("Rétention vs N-1", pct(r), "Dernière campagne sélectionnée ; vide pour 2019 ou une OP nouvelle"),
          ("Femmes", pct(s.femmes / s.n), None), ("Jeunes 15-35 ans", pct(s.jeunes / s.n), None)])
    ops = OPS if op == "Toutes" else [op]
    col1, col2 = st.columns([7, 5])
    with col1, st.container(border=True):
        st.markdown("**Producteurs par campagne et coopérative**")
        couleurs = {"CKK": C["vert"], "COOKKANZ": C["cafe"], "COOKURU": C["ambre"], "COOPADE": C["ardoise"]}
        fig = go.Figure()
        for o in ops:
            d = CAFE[CAFE.op == o]
            fig.add_bar(x=d.annee.astype(str), y=d.n, name=o, marker_color=couleurs[o], hovertemplate="%{x} : %{y:,}<extra>" + o + "</extra>")
        graphique(fig_base(fig, barmode="stack"))
    with col2, st.container(border=True):
        st.markdown("**Part des femmes et des jeunes (15-35 ans)**")
        g = CAFE[CAFE.op.isin(ops)].groupby("annee")[["n", "femmes", "jeunes"]].sum()
        fig = go.Figure()
        fig.add_scatter(x=g.index.astype(str), y=g.jeunes / g.n, name="Jeunes 15-35 ans", mode="lines+markers", line=dict(color=C["vert"], width=3))
        fig.add_scatter(x=g.index.astype(str), y=g.femmes / g.n, name="Femmes", mode="lines+markers", line=dict(color=C["cafe"], width=3))
        graphique(fig_base(fig, yaxis=dict(tickformat=".0%", range=[0, 0.7]), hovermode="x unified"))

    col1, col2 = st.columns([8, 4])
    with col1, st.container(border=True):
        st.markdown("**Profil des coopératives**")
        st.caption("Selon la campagne sélectionnée · en rouge : femmes sous 15 % ou jeunes sous 30 %")
        lignes = []
        for o in OPS + ["Ensemble"]:
            oo = "Toutes" if o == "Ensemble" else o
            x = somme(filtre_cafe(annee, oo))
            if x.n:
                lignes.append({"Coopérative": o, "Producteurs": int(x.n), "Femmes": x.femmes / x.n, "Jeunes": x.jeunes / x.n,
                               "Ha moyen": x.sup / x.n, "Conformes": x.conforme / x.n, "Rétention": retention(annee, oo)})
        tab = pd.DataFrame(lignes)
        styl = (tab.style.format({"Producteurs": fr0, "Femmes": pct, "Jeunes": pct, "Ha moyen": fr2, "Conformes": pct, "Rétention": pct})
                .map(lambda v: f"color: {C['rouge']}; font-weight: 600" if v < 0.15 else "", subset=["Femmes"])
                .map(lambda v: f"color: {C['rouge']}; font-weight: 600" if v < 0.30 else "", subset=["Jeunes"]))
        st.dataframe(styl, hide_index=True)
    with col2, st.container(border=True):
        st.markdown("**Statut de certification bio / fairtrade**")
        fig = go.Figure(go.Pie(labels=["Conforme", "En conversion", "Non conforme", "Non renseigné"],
                               values=[s.conforme, s.conversion, s.non_conforme, s.non_renseigne], hole=0.6, sort=False,
                               marker_colors=[C["vert"], C["ambre"], C["rouge"], C["gris"]], textinfo="percent"))
        graphique(fig_base(fig, height=280))
    st.caption(f"Rétention = producteurs de N-1 présents en N. {fr0(D['fideles7'])} producteurs sont présents sur les 7 campagnes.")


def page_economie():
    st.title("Café : production et économie")
    annee, op = filtres_cafe("e")
    s = somme(filtre_cafe(annee, op))
    kpis([("Superficie déclarée (ha)", fr0(s.sup), None), ("Superficie moyenne (ha)", fr2(s.sup / s.n), "Donnée déclarée, la plus fiable"),
          ("Production estimée (t cerise)", fr0(s.prod_t), "ESTIMÉE : superficie × densité × rendement par pied"),
          ("CA estimé (M USD)", fr1(s.ca / 1e6), "ESTIMÉ : production × 0,55 USD/kg"),
          ("Marge estimée / producteur (USD)", fr0(s.marge / s.n), "Forfait : 60 % du CA")])
    ops = OPS if op == "Toutes" else [op]
    g = CAFE[CAFE.op.isin(ops)].groupby("annee")[["sup", "prod_t", "marge", "n"]].sum()
    col1, col2 = st.columns(2)
    with col1, st.container(border=True):
        st.markdown("**Superficie déclarée et production estimée**")
        st.caption("La production estimée croît 2,4 fois plus vite que la superficie : effet des paramètres de rendement")
        fig = go.Figure()
        fig.add_bar(x=g.index.astype(str), y=g.sup, name="Superficie déclarée (ha)", marker_color=C["sauge"])
        fig.add_scatter(x=g.index.astype(str), y=g.prod_t, name="Production estimée (t cerise)", mode="lines+markers", line=dict(color=C["cafe"], width=3))
        graphique(fig_base(fig))
    with col2, st.container(border=True):
        st.markdown("**Marge estimée par producteur (USD)**")
        st.caption("Marge = 60 % du CA pour 100 % des lignes : indicateur forfaitaire")
        mg = g.marge / g.n
        fig = go.Figure(go.Bar(x=g.index.astype(str), y=mg, marker_color=C["ambre"], text=[fr0(v) for v in mg], textposition="outside"))
        graphique(fig_base(fig, yaxis=dict(range=[0, mg.max() * 1.18])))
    st.error("**Pourquoi ces chiffres ne mesurent pas l'impact**\n\n"
             "- Production = superficie × densité × rendement par pied ; les deux paramètres changent chaque année (1 000 → 1 620 pieds/ha ; 1,5 → 2,5 kg/pied).\n"
             "- Chiffre d'affaires = production × 0,55 USD/kg, un prix unique sur 7 ans.\n"
             "- Coût = 40 % et marge = 60 % du CA pour 100 % des lignes.\n\n"
             "Seule la superficie (0,55 ha en moyenne, stable) est déclarée. **Recommandation : collecter les ventes réelles par producteur.**",
             icon=":material/warning:")


def page_cacao():
    st.title("Cacao : revenu des ménages et écart au revenu vital")
    with st.sidebar:
        st.subheader("Filtres")
        section = st.selectbox("Section", ["Toutes"] + SECTIONS, key="c_section")
        st.caption("Enquête Living Income, 88 ménages Cacao Okapi, mars 2024. Échantillon indicatif (6 ménages dirigés par des femmes).")
    m = MEN if section == "Toutes" else MEN[MEN.Section == section]
    s = stats_cacao(m)
    kpis([("Revenu net médian (USD/an)", fr0(s["rev"]), None), ("Seuil revenu vital (USD/an)", fr0(D["seuil"]), "Anker 2025, ménage de 6 personnes"),
          ("Au-dessus du seuil (réf.)", pct(s["ref"], 0), None), ("Au-dessus du seuil ajusté", pct(s["adj"], 0), None),
          ("Écart médian au seuil ajusté (USD/an)", fr0(s["ecart"]), "Ménages sous le seuil"), ("Revenu / personne / jour (USD)", fr2(s["pcj"]), "Médiane")])
    col1, col2 = st.columns(2)
    with col1, st.container(border=True):
        st.markdown("**Revenu net médian par section (USD/an)**")
        st.caption("Ligne pointillée : seuil de revenu vital")
        t = MEN.groupby("Section").Revenu_Net_Total_USD.median().sort_values(ascending=False)
        coul = [C["vert"] if section in ("Toutes", sec) else C["sauge"] for sec in t.index]
        fig = go.Figure(go.Bar(x=t.index, y=t.values, marker_color=coul, text=[fr0(v) for v in t.values], textposition="outside"))
        fig.add_hline(y=D["seuil"], line_dash="dash", line_color=C["rouge"], annotation_text=f"Seuil {fr0(D['seuil'])}", annotation_position="top left")
        graphique(fig_base(fig, yaxis=dict(range=[0, 6000])))
    with col2, st.container(border=True):
        st.markdown("**Composition du revenu net**")
        st.caption("Forte dépendance au cacao : un choc de prix touche tout le revenu")
        parts = pd.Series({lab: m[k].sum() / m.Revenu_Net_Total_USD.sum() for k, lab in SOURCES.items()})[::-1]
        fig = go.Figure(go.Bar(y=parts.index, x=parts.values, orientation="h", text=[pct(v) for v in parts.values], textposition="outside",
                               marker_color=[C["cafe"] if i == "Cacao" else C["sable"] for i in parts.index]))
        graphique(fig_base(fig, xaxis=dict(tickformat=".0%", range=[-0.05, 1.1])))
    kpis([("Part du cacao dans le revenu", pct(s["part_cacao"], 0), None), ("Sous 2,15 USD / pers. / jour", pct(s["sous215"], 0), "Seuil Banque mondiale, PPA 2017"),
          ("Dépenses supérieures au revenu", pct(s["solde"], 0), None), ("Personnes par ménage", fr1(s["taille"]), "Contre 6 dans le ménage de référence")])
    col1, col2 = st.columns(2)
    with col1, st.container(border=True):
        st.markdown("**Leviers : rendement, prix, taille du ménage**")
        st.caption("Mayuano : rendement ×2 mais prix ÷2")
        lev = MEN.groupby("Section").agg(**{"Ménages": ("Taille_Menage", "size"), "Taille": ("Taille_Menage", "mean"),
                                            "Ha cacao": ("Superficie_Cacao_ha", "median"), "kg/ha": ("Rendement_kg_ha", "median"),
                                            "USD/kg": ("Prix_kg_USD", "median")}).reset_index()
        st.dataframe(lev.style.format({"Taille": fr1, "Ha cacao": fr1, "kg/ha": fr0, "USD/kg": fr2}), hide_index=True)
    with col2, st.container(border=True):
        st.markdown("**Base planteurs Cacao Okapi (301 planteurs)**")
        st.caption("Liste officielle des planteurs par section")
        ok = D["okapi"].assign(ha_pl=lambda x: x.sup_cacao / x.planteurs, part=lambda x: x.sup_cacao / x.sup_tot)
        ok = ok.rename(columns={"section": "Section", "planteurs": "Planteurs", "sup_cacao": "Ha cacao", "ha_pl": "Ha / planteur", "part": "% foncier en cacao"})
        st.dataframe(ok[["Section", "Planteurs", "Ha cacao", "Ha / planteur", "% foncier en cacao"]]
                     .style.format({"Ha cacao": fr0, "Ha / planteur": fr1, "% foncier en cacao": lambda v: pct(v, 0)}), hide_index=True)
    st.caption("Revenu net = cacao + café + agroforesterie + autres cultures + élevage + hors ferme + transferts. "
               "La variable « living_income » du questionnaire (revenu − dépenses) n'est pas un revenu.")


def page_qualite():
    st.title("Qualité des données : diagnostic pour la validation")
    with st.sidebar:
        st.subheader("Filtres")
        base = st.selectbox("Base", ["Toutes"] + list(QUAL.Source.unique()), key="q_base")
        grav = st.selectbox("Gravité", ["Toutes"] + GRAVITES, key="q_grav")
    q = QUAL[((QUAL.Source == base) | (base == "Toutes")) & ((QUAL.Gravite == grav) | (grav == "Toutes"))].copy()
    q = q.assign(o=q.Gravite.map({g: i for i, g in enumerate(GRAVITES)})).sort_values(["o", "ID"])
    a = CAFE[["n", "territoire_ok", "doublon"]].sum()
    kpis([("Contrôles affichés", str(len(q)), None), ("Critiques", str((q.Gravite == "Critique").sum()), None),
          ("Gravité élevée", str((q.Gravite == "Élevée").sum()), None), ("Territoire renseigné (café)", pct(a.territoire_ok / a.n), "Toutes campagnes"),
          ("Cartes en doublon (café)", pct(a.doublon / a.n), "Toutes campagnes")])
    st.info("**Avis proposé pour le PV : validation partielle.** La base café est valide comme référentiel des bénéficiaires "
            "(effectifs, genre, âge, coopérative), pas pour ses indicateurs économiques.", icon=":material/fact_check:")
    col1, col2 = st.columns([8, 4])
    with col1, st.container(border=True):
        st.markdown("**Registre des contrôles qualité**")
        tab = q.rename(columns={"Gravite": "Gravité", "Source": "Base", "Controle": "Contrôle", "Nb_Anomalies": "Anomalies", "Commentaire": "Impact"})
        tab = tab[["Gravité", "Base", "Contrôle", "Anomalies", "Taux", "Impact"]]
        couleur = {"Critique": C["rouge"], "Élevée": C["rouge"], "Moyenne": C["ambre"], "Faible": C["vert"]}
        st.dataframe(tab.style.format({"Anomalies": fr0, "Taux": pct}, na_rep="")
                     .map(lambda v: f"color: {couleur.get(v, '')}; font-weight: 600", subset=["Gravité"]), hide_index=True)
    with col2, st.container(border=True):
        st.markdown("**Contrôles par dimension**")
        dim = q.Dimension.value_counts().sort_values()
        fig = go.Figure(go.Bar(y=dim.index, x=dim.values, orientation="h", marker_color=C["ardoise"], text=dim.values, textposition="outside"))
        graphique(fig_base(fig, height=260, xaxis=dict(dtick=1)))
    st.caption("Détail complet : data/qualite_controles.csv du dépôt GitHub.")


pages = st.navigation([
    st.Page(page_synthese, title="Synthèse", icon=":material/dashboard:", default=True),
    st.Page(page_beneficiaires, title="Café · Bénéficiaires", icon=":material/groups:", url_path="beneficiaires"),
    st.Page(page_economie, title="Café · Économie", icon=":material/payments:", url_path="economie"),
    st.Page(page_cacao, title="Cacao · Revenu vital", icon=":material/eco:", url_path="cacao"),
    st.Page(page_qualite, title="Qualité des données", icon=":material/fact_check:", url_path="qualite"),
])
with st.sidebar:
    st.markdown("**Rikolto RDC · Café & Cacao**")
    st.caption("Données pseudonymisées · analyse septembre 2026")
    st.markdown("[Code source et rapport](https://github.com/lucienbzr-debug/rikolto-cafe-cacao-2019-2025)")
pages.run()
