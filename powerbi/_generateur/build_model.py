# -*- coding: utf-8 -*-
"""Génère le modèle sémantique TMDL du tableau de bord Rikolto Café & Cacao."""
import os, uuid, textwrap

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NAME = "Rikolto_Cafe_Cacao"
DATA_DIR = os.path.abspath(os.path.join(ROOT, "..", "data")) + "\\"
SM = os.path.join(ROOT, f"{NAME}.SemanticModel")
DEF = os.path.join(SM, "definition")
os.makedirs(os.path.join(DEF, "tables"), exist_ok=True)
os.makedirs(os.path.join(DEF, "cultures"), exist_ok=True)

T = "\t"

def w(path, txt):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(txt)

def q(name):
    """Quote a TMDL object name when needed."""
    if any(c in name for c in " .=:'-()%/’,&+") or not name.isascii():
        return "'" + name.replace("'", "''") + "'"
    return name

# M type -> TMDL dataType
MT = {"int": ("Int64.Type", "int64"), "dec": ("Currency.Type", "decimal"), "txt": ("type text", "string")}

def table(name, desc, csv, cols, measures, extra_m=None, extra_cols=None):
    """cols: list of dict(name, src, t, hidden, summ, fmt, desc, sortBy)"""
    out = []
    for d in desc.split("\n"):
        out.append(f"/// {d}")
    out.append(f"table {q(name)}")
    out.append("")
    for m in measures:
        for d in m["desc"].split("\n"):
            out.append(f"{T}/// {d}")
        expr = m["expr"].strip()
        if "\n" in expr:
            body = textwrap.indent(expr, T * 3)
            out.append(f"{T}measure {q(m['name'])} = ```")
            out.append(body)
            out.append(f"{T*3}```")
        else:
            out.append(f"{T}measure {q(m['name'])} = {expr}")
        out.append(f"{T*2}formatString: {m['fmt']}")
        if m.get("folder"):
            out.append(f"{T*2}displayFolder: {m['folder']}")
        out.append("")
    for c in cols + (extra_cols or []):
        if c.get("desc"):
            out.append(f"{T}/// {c['desc']}")
        out.append(f"{T}column {q(c['name'])}")
        out.append(f"{T*2}dataType: {MT[c['t']][1]}")
        if c.get("hidden"):
            out.append(f"{T*2}isHidden")
        if c.get("fmt"):
            out.append(f"{T*2}formatString: {c['fmt']}")
        out.append(f"{T*2}summarizeBy: {c.get('summ', 'none')}")
        out.append(f"{T*2}sourceColumn: {c.get('src', c['name'])}")
        if c.get("sortBy"):
            out.append(f"{T*2}sortByColumn: {q(c['sortBy'])}")
        out.append("")
    # Partition
    if csv:
        types = ", ".join('{"%s", %s}' % (c.get("src", c["name"]), MT[c["t"]][0]) for c in cols)
        keep = ", ".join('"%s"' % c.get("src", c["name"]) for c in cols)
        m = [
            "let",
            f'    // Lecture du fichier CSV nettoyé produit par l\'analyse',
            f'    #"Fichier lu" = Csv.Document(File.Contents(DossierDonnees & "{csv}"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),',
            f'    #"En-têtes promus" = Table.PromoteHeaders(#"Fichier lu", [PromoteAllScalars = true]),',
            f'    #"Colonnes retenues" = Table.SelectColumns(#"En-têtes promus", {{{keep}}}),',
            f'    #"Types appliqués" = Table.TransformColumnTypes(#"Colonnes retenues", {{{types}}}, "en-US")',
        ]
        last = '#"Types appliqués"'
        for step in (extra_m or []):
            m[-1] += ","
            m.append(f'    {step[0]} = {step[1].replace("__PREV__", last)}')
            last = step[0]
        m += ["in", f"    {last}"]
    else:
        m = extra_m
    out.append(f"{T}partition {q(name)} = m")
    out.append(f"{T*2}mode: import")
    out.append(f"{T*2}source =")
    for line in m:
        out.append(T * 4 + line)
    out.append("")
    w(os.path.join(DEF, "tables", f"{name}.tmdl"), "\n".join(out) + "\n")


def C(name, src, t, **kw):
    d = dict(name=name, src=src, t=t); d.update(kw); return d

# ---------------------------------------------------------------- Campagne
w(os.path.join(DEF, "tables", "Campagne.tmdl"), "\n".join([
    "/// Dimension des campagnes caféières annuelles 2019-2025 (une ligne par campagne).",
    "table Campagne",
    "",
    f"{T}/// Année de la campagne (clé de relation).",
    f"{T}column Année",
    f"{T*2}dataType: int64",
    f"{T*2}isKey",
    f"{T*2}formatString: 0",
    f"{T*2}summarizeBy: none",
    f"{T*2}sourceColumn: Année",
    "",
    f"{T}/// Libellé texte de la campagne, trié chronologiquement.",
    f"{T}column 'Libellé campagne'",
    f"{T*2}dataType: string",
    f"{T*2}summarizeBy: none",
    f"{T*2}sourceColumn: Libellé campagne",
    f"{T*2}sortByColumn: Année",
    "",
    f"{T}partition Campagne = m",
    f"{T*2}mode: import",
    f"{T*2}source =",
    f"{T*4}let",
    f"{T*4}    #\"Liste des années\" = Table.FromList({{2019..2025}}, Splitter.SplitByNothing(), {{\"Année\"}}),",
    f"{T*4}    #\"Type entier\" = Table.TransformColumnTypes(#\"Liste des années\", {{{{\"Année\", Int64.Type}}}}),",
    f"{T*4}    #\"Libellé ajouté\" = Table.AddColumn(#\"Type entier\", \"Libellé campagne\", each Text.From([Année]), type text)",
    f"{T*4}in",
    f"{T*4}    #\"Libellé ajouté\"",
    "",
]) + "\n")

# ---------------------------------------------------------------- Café
PC = "'Producteurs café'"
cafe_cols = [
    C("ID saison", "ID_Saison", "txt", hidden=True, desc="Identifiant unique producteur × campagne."),
    C("ID producteur", "ID_Producteur", "int", hidden=True, desc="Identifiant longitudinal consolidé (Nom + Sexe + OP) sur 2019-2025."),
    C("Sexe", "Sexe", "txt", desc="Sexe du bénéficiaire."),
    C("Âge", "Age", "int", summ="none", desc="Âge déclaré lors de la campagne."),
    C("Catégorie d’âge", "Classe_Age", "txt", desc="Jeune (15-35 ans) ou Adulte (36 ans et +)."),
    C("Coopérative", "Cooperative", "txt", desc="Organisation paysanne de base (CKK, COOKKANZ, COOPADE, COOKURU)."),
    C("Village", "Village", "txt", desc="Village du bénéficiaire (22 % non renseigné)."),
    C("Collectivité", "Collectivite", "txt", desc="Collectivité administrative (45 % non renseignée)."),
    C("Territoire", "Territoire", "txt", desc="Territoire administratif ; 'Non renseigné' pour 36 % des lignes."),
    C("Année", "Annee", "int", hidden=True, desc="Année de campagne (clé vers Campagne)."),
    C("Carte membre", "Carte_Membre", "txt", hidden=True, desc="Numéro de carte de membre."),
    C("Superficie ha", "Superficie_ha", "dec", hidden=True, desc="Superficie cultivée déclarée (ha)."),
    C("Production cerise kg", "Production_Cerise_kg", "dec", hidden=True, desc="Production ESTIMÉE = superficie × densité × rendement/pied (paramètres fixes)."),
    C("CA USD", "CA_USD", "dec", hidden=True, desc="Chiffre d'affaires ESTIMÉ = production × 0,55 USD."),
    C("Coût USD", "Cout_USD", "dec", hidden=True, desc="Coût forfaitaire = 40 % du CA."),
    C("Marge USD", "Marge_USD", "dec", hidden=True, desc="Marge forfaitaire = 60 % du CA."),
    C("Certification", "Certification", "txt", desc="Statut bio / fairtrade : Conforme, En conversion, Non conforme, Non renseigné."),
    C("Nouveau", "Nouveau", "int", hidden=True, desc="1 lors de la première apparition du producteur sur 2019-2025."),
    C("Présent N-1", "Present_N_1", "int", hidden=True, desc="1 si le producteur était aussi présent la campagne précédente."),
    C("Nb campagnes de présence", "Nb_Annees_Presence", "int", desc="Nombre de campagnes où le producteur apparaît (1 à 7)."),
    C("Carte en doublon", "Flag_Carte_Doublon", "int", hidden=True, desc="1 si la carte membre est partagée par plusieurs lignes de la même campagne."),
    C("Âge incohérent", "Flag_Age_Incoherent", "int", hidden=True, desc="1 si l'âge varie de plus de 2 ans par rapport à l'écart de campagnes."),
]
cafe_meas = [
    dict(name="Producteurs", expr=f"COUNTROWS({PC})", fmt="#,##0", folder="Bénéficiaires",
         desc="Nombre de producteurs enregistrés (une ligne par producteur et par campagne)."),
    dict(name="Producteurs uniques", expr=f"DISTINCTCOUNT({PC}[ID producteur])", fmt="#,##0", folder="Bénéficiaires",
         desc="Nombre de personnes distinctes (identifiant longitudinal) sur la période filtrée."),
    dict(name="Femmes", expr=f"CALCULATE([Producteurs], {PC}[Sexe] = \"Femme\")", fmt="#,##0", folder="Inclusion",
         desc="Nombre de productrices."),
    dict(name="% femmes", expr="DIVIDE([Femmes], [Producteurs])", fmt="0.0%", folder="Inclusion",
         desc="Part des femmes parmi les producteurs."),
    dict(name="% jeunes (15-35 ans)", expr=f"""
DIVIDE(
    CALCULATE([Producteurs], {PC}[Catégorie d’âge] = "Jeune (15-35)"),
    CALCULATE([Producteurs], NOT ISBLANK({PC}[Catégorie d’âge]))
)""", fmt="0.0%", folder="Inclusion", desc="Part des 15-35 ans parmi les producteurs dont l'âge est connu."),
    dict(name="Superficie totale (ha)", expr=f"SUM({PC}[Superficie ha])", fmt="#,##0", folder="Production",
         desc="Superficie caféière totale déclarée."),
    dict(name="Superficie moyenne (ha)", expr=f"AVERAGE({PC}[Superficie ha])", fmt="0.00", folder="Production",
         desc="Superficie moyenne par producteur (donnée déclarée, non estimée)."),
    dict(name="Production estimée (t cerise)", expr=f"DIVIDE(SUM({PC}[Production cerise kg]), 1000)", fmt="#,##0", folder="Économie (estimations)",
         desc="Production de cerise ESTIMÉE par modèle (superficie × densité × rendement/pied). Ne pas présenter comme une production mesurée."),
    dict(name="CA estimé (USD)", expr=f"SUM({PC}[CA USD])", fmt="#,##0", folder="Économie (estimations)",
         desc="Chiffre d'affaires ESTIMÉ = production estimée × 0,55 USD/kg (prix unique 2019-2025)."),
    dict(name="Marge estimée (USD)", expr=f"SUM({PC}[Marge USD])", fmt="#,##0", folder="Économie (estimations)",
         desc="Marge forfaitaire = 60 % du CA estimé. Aucun coût réel n'est collecté."),
    dict(name="Marge estimée par producteur (USD)", expr="DIVIDE([Marge estimée (USD)], [Producteurs])", fmt="#,##0", folder="Économie (estimations)",
         desc="Marge forfaitaire moyenne par producteur."),
    dict(name="% certifiés conformes", expr=f"DIVIDE(CALCULATE([Producteurs], {PC}[Certification] = \"Conforme\"), [Producteurs])", fmt="0.0%", folder="Certification",
         desc="Part des producteurs au statut bio/fairtrade Conforme (les non renseignés restent au dénominateur)."),
    dict(name="% certification non renseignée", expr=f"DIVIDE(CALCULATE([Producteurs], {PC}[Certification] = \"Non renseigné\"), [Producteurs])", fmt="0.0%", folder="Qualité",
         desc="Part des producteurs sans statut de certification saisi."),
    dict(name="Nouveaux producteurs", expr=f"SUM({PC}[Nouveau])", fmt="#,##0", folder="Bénéficiaires",
         desc="Producteurs apparaissant pour la première fois dans la base."),
    dict(name="Producteurs N-1", expr=f"""
VAR AnneeCourante = MAX(Campagne[Année])
RETURN
    CALCULATE([Producteurs], REMOVEFILTERS(Campagne), Campagne[Année] = AnneeCourante - 1)""", fmt="#,##0", folder="Bénéficiaires",
         desc="Nombre de producteurs lors de la campagne précédant la campagne sélectionnée."),
    dict(name="Taux de rétention", expr=f"""
VAR AnneeCourante = MAX(Campagne[Année])
VAR BaseN1 = [Producteurs N-1]
RETURN
    IF(
        BaseN1 >= 30,
        DIVIDE(
            CALCULATE(SUM({PC}[Présent N-1]), REMOVEFILTERS(Campagne), Campagne[Année] = AnneeCourante),
            BaseN1
        )
    )""", fmt="0.0%", folder="Bénéficiaires",
         desc="Part des producteurs de la campagne N-1 toujours présents en N. Plusieurs campagnes sélectionnées : calculé sur la plus récente. Vide si moins de 30 producteurs en N-1 (coopérative nouvelle)."),
    dict(name="Croissance vs N-1", expr="DIVIDE([Producteurs] - [Producteurs N-1], [Producteurs N-1])", fmt="+0.0%;-0.0%;0.0%", folder="Bénéficiaires",
         desc="Évolution du nombre de producteurs par rapport à la campagne précédente."),
    dict(name="% territoire renseigné", expr=f"DIVIDE(CALCULATE([Producteurs], {PC}[Territoire] <> \"Non renseigné\"), [Producteurs])", fmt="0.0%", folder="Qualité",
         desc="Taux de complétude du champ Territoire."),
    dict(name="% cartes en doublon", expr=f"DIVIDE(SUM({PC}[Carte en doublon]), [Producteurs])", fmt="0.0%", folder="Qualité",
         desc="Part des lignes dont la carte membre est partagée avec une autre ligne de la même campagne."),
    dict(name="Fidèles 7 campagnes", expr=f"CALCULATE([Producteurs uniques], {PC}[Nb campagnes de présence] = 7)", fmt="#,##0", folder="Bénéficiaires",
         desc="Producteurs présents lors des 7 campagnes 2019-2025."),
]
table("Producteurs café",
      "Base consolidée Rikolto des producteurs de café 2019-2025 (une ligne par producteur et par campagne).\nLes variables économiques sont des ESTIMATIONS par paramètres fixes, pas des mesures terrain.",
      "fact_cafe_producteurs.csv", cafe_cols, cafe_meas)

# ---------------------------------------------------------------- Cacao ménages
MC = "'Ménages cacao'"
LI = "[Seuil revenu vital (USD/an)]"
men_cols = [
    C("ID ménage", "ID_Menage", "int", hidden=True, desc="Identifiant du ménage enquêté."),
    C("Section", "Section", "txt", desc="Section Cacao Okapi (Babungwe, Mambasa, Mayuano, Mungamba)."),
    C("Sexe", "Sexe", "txt", desc="Sexe du chef de ménage enquêté."),
    C("Âge", "Age", "int", desc="Âge du répondant."),
    C("Taille ménage", "Taille_Menage", "int", hidden=True, desc="Nombre de membres du ménage."),
    C("Superficie cacao ha", "Superficie_Cacao_ha", "dec", hidden=True, desc="Superficie cacao totale du ménage."),
    C("Rendement kg ha", "Rendement_kg_ha", "dec", hidden=True, desc="Production cacao / superficie productive."),
    C("Prix kg USD", "Prix_kg_USD", "dec", hidden=True, desc="Recette cacao / quantité vendue."),
    C("Revenu net total USD", "Revenu_Net_Total_USD", "dec", hidden=True, desc="Somme des revenus nets : cacao, café, agroforesterie, autres cultures, élevage, hors ferme, transferts."),
    C("Solde revenu dépenses USD", "Solde_Revenu_Depenses_USD", "dec", hidden=True, desc="Variable 'living_income' du questionnaire = revenu net − dépenses déclarées du ménage."),
    C("Seuil ajusté USD", "Seuil_LI_Ajuste_USD", "dec", hidden=True, desc="Seuil de revenu vital proportionnel à la taille du ménage (2 628 / 6 × taille)."),
    C("Revenu cacao USD", "Rev_Cacao", "dec", hidden=True, desc="Revenu net cacao."),
    C("Atteint revenu vital", "Atteint_LI_Menage_Ref", "int", hidden=True, desc="1 si revenu net ≥ 2 628 USD/an (ménage de référence Anker 6 personnes)."),
    C("Atteint revenu vital ajusté", "Atteint_LI_Ajuste_Taille", "int", hidden=True, desc="1 si revenu net ≥ seuil ajusté à la taille réelle du ménage."),
    C("Revenu par personne et par jour", "Revenu_par_personne_jour", "dec", hidden=True, desc="Revenu net / taille du ménage / 365."),
    C("Valeur extrême", "Flag_Outlier", "int", desc="1 si revenu, rendement ou prix extrême (à vérifier sur le terrain)."),
]
men_meas = [
    dict(name="Ménages enquêtés", expr=f"COUNTROWS({MC})", fmt="#,##0", folder="Échantillon", desc="Nombre de ménages cacao enquêtés (enquête Living Income, mars 2024)."),
    dict(name="Seuil revenu vital (USD/an)", expr="LOOKUPVALUE('Paramètres'[Valeur], 'Paramètres'[Paramètre], \"Seuil revenu vital ménage (USD/an)\")", fmt="#,##0",
         folder="Revenu vital", desc="Benchmark Anker RDC rurale 2025 : 219 USD/mois pour un ménage de référence de 6 personnes."),
    dict(name="Revenu net médian (USD/an)", expr=f"MEDIAN({MC}[Revenu net total USD])", fmt="#,##0", folder="Revenu vital", desc="Revenu net annuel médian du ménage, toutes sources."),
    dict(name="Revenu net moyen (USD/an)", expr=f"AVERAGE({MC}[Revenu net total USD])", fmt="#,##0", folder="Revenu vital", desc="Moyenne tirée vers le haut par quelques très grands producteurs ; préférer la médiane."),
    dict(name="% au-dessus du revenu vital", expr=f"AVERAGE({MC}[Atteint revenu vital])", fmt="0%", folder="Revenu vital",
         desc="Part des ménages dont le revenu net atteint le seuil Anker (ménage de référence de 6 personnes)."),
    dict(name="% au-dessus du revenu vital (ajusté taille)", expr=f"AVERAGE({MC}[Atteint revenu vital ajusté])", fmt="0%", folder="Revenu vital",
         desc="Même indicateur, seuil proportionnel à la taille réelle du ménage (10,3 personnes en moyenne) : vision prudente."),
    dict(name="Écart médian au revenu vital (USD)", expr=f"""
VAR Seuil = {LI}
RETURN
    MEDIANX(
        FILTER({MC}, {MC}[Revenu net total USD] < Seuil),
        Seuil - {MC}[Revenu net total USD]
    )""", fmt="#,##0", folder="Revenu vital", desc="Pour les ménages sous le seuil : revenu annuel supplémentaire médian nécessaire."),
    dict(name="Écart médian au revenu vital ajusté (USD)", expr=f"""
MEDIANX(
    FILTER({MC}, {MC}[Revenu net total USD] < {MC}[Seuil ajusté USD]),
    {MC}[Seuil ajusté USD] - {MC}[Revenu net total USD]
)""", fmt="#,##0", folder="Revenu vital", desc="Pour les ménages sous le seuil ajusté à leur taille : revenu annuel supplémentaire médian nécessaire (indicateur bailleur n°8)."),
    dict(name="Revenu médian par personne et par jour (USD)", expr=f"MEDIAN({MC}[Revenu par personne et par jour])", fmt="0.00", folder="Revenu vital",
         desc="Revenu net par membre du ménage et par jour."),
    dict(name="% sous 2,15 USD par personne et par jour", expr=f"DIVIDE(COUNTROWS(FILTER({MC}, {MC}[Revenu par personne et par jour] < 2.15)), [Ménages enquêtés])", fmt="0%",
         folder="Revenu vital", desc="Part des ménages sous le seuil de pauvreté extrême de la Banque mondiale."),
    dict(name="Part du cacao dans le revenu", expr=f"DIVIDE(SUM({MC}[Revenu cacao USD]), SUM({MC}[Revenu net total USD]))", fmt="0%", folder="Revenu vital",
         desc="Dépendance au cacao : part du revenu net total provenant du cacao."),
    dict(name="% ménages dépenses supérieures au revenu", expr=f"DIVIDE(COUNTROWS(FILTER({MC}, {MC}[Solde revenu dépenses USD] < 0)), [Ménages enquêtés])", fmt="0%",
         folder="Revenu vital", desc="Ménages dont les dépenses déclarées dépassent le revenu net."),
    dict(name="Rendement médian (kg/ha)", expr=f"MEDIAN({MC}[Rendement kg ha])", fmt="#,##0", folder="Production", desc="Rendement cacao médian par hectare productif."),
    dict(name="Prix médian (USD/kg)", expr=f"MEDIAN({MC}[Prix kg USD])", fmt="0.00", folder="Production", desc="Prix de vente médian du cacao."),
    dict(name="Taille moyenne du ménage", expr=f"AVERAGE({MC}[Taille ménage])", fmt="0.0", folder="Échantillon", desc="Nombre moyen de personnes par ménage."),
    dict(name="Superficie cacao médiane (ha)", expr=f"MEDIAN({MC}[Superficie cacao ha])", fmt="0.0", folder="Production", desc="Superficie cacao médiane par ménage."),
]
table("Ménages cacao",
      "Enquête Living Income auprès de 88 ménages cacao Cacao Okapi (RDC, mars 2024), une ligne par ménage.",
      "fact_cacao_menages.csv", men_cols, men_meas)

# ---------------------------------------------------------------- Sources de revenu
SR = "'Sources de revenu cacao'"
table("Sources de revenu cacao",
      "Décomposition du revenu net de chaque ménage cacao par source (format long).",
      "fact_cacao_sources_revenu.csv",
      [C("ID ménage", "ID_Menage", "int", hidden=True, desc="Clé vers Ménages cacao."),
       C("Source", "Source", "txt", desc="Source de revenu.", sortBy="Ordre"),
       C("Ordre", "Ordre", "int", hidden=True, desc="Ordre d'affichage des sources."),
       C("Montant USD", "Montant_USD", "dec", hidden=True, desc="Revenu net annuel de la source.")],
      [dict(name="Revenu net par source (USD)", expr=f"SUM({SR}[Montant USD])", fmt="#,##0", folder="Revenu", desc="Revenu net annuel cumulé par source."),
       dict(name="Part de la source", expr=f"DIVIDE([Revenu net par source (USD)], CALCULATE([Revenu net par source (USD)], REMOVEFILTERS({SR}[Source], {SR}[Ordre])))", fmt="0.0%",
            folder="Revenu", desc="Part de la source dans le revenu net total.")])

# ---------------------------------------------------------------- Okapi
OK = "'Planteurs Okapi'"
table("Planteurs Okapi",
      "Liste des 301 planteurs de la coopérative Cacao Okapi (une ligne par planteur).",
      "fact_cacao_okapi_planteurs.csv",
      [C("Code planteur", "Code_Planteur", "txt", hidden=True, desc="Code planteur (28 codes en doublon)."),
       C("Section", "Section", "txt", desc="Section / onglet de la liste."),
       C("Axe", "Axe", "txt", desc="Axe géographique."),
       C("Corporation", "Corporation", "txt", desc="Corporation de base."),
       C("Superficie totale ha", "Superficie_Totale_ha", "dec", hidden=True, desc="Superficie totale du champ."),
       C("Superficie cacao ha", "Superficie_Cacao_ha", "dec", hidden=True, desc="Superficie en cacao."),
       C("Code en doublon", "Flag_Code_Doublon", "int", hidden=True, desc="1 si le code planteur est en doublon.")],
      [dict(name="Planteurs Okapi", expr=f"COUNTROWS({OK})", fmt="#,##0", folder="Planteurs", desc="Nombre de planteurs listés."),
       dict(name="Superficie cacao Okapi (ha)", expr=f"SUM({OK}[Superficie cacao ha])", fmt="#,##0", folder="Planteurs", desc="Superficie cacao totale déclarée."),
       dict(name="Superficie cacao moyenne Okapi (ha)", expr=f"AVERAGE({OK}[Superficie cacao ha])", fmt="0.0", folder="Planteurs", desc="Superficie cacao moyenne par planteur."),
       dict(name="Part du foncier en cacao", expr=f"DIVIDE(SUM({OK}[Superficie cacao ha]), SUM({OK}[Superficie totale ha]))", fmt="0%", folder="Planteurs",
            desc="Superficie cacao / superficie totale des champs."),
       dict(name="Codes planteurs en doublon", expr=f"SUM({OK}[Code en doublon])", fmt="#,##0", folder="Qualité", desc="Lignes dont le code planteur apparaît plusieurs fois.")])

# ---------------------------------------------------------------- Qualité
CQ = "'Contrôles qualité'"
table("Contrôles qualité",
      "Registre des contrôles qualité réalisés sur les trois bases (une ligne par contrôle).",
      "qualite_controles.csv",
      [C("ID contrôle", "ID", "int", hidden=True, desc="Numéro du contrôle."),
       C("Base", "Source", "txt", desc="Base contrôlée."),
       C("Dimension", "Dimension", "txt", desc="Dimension qualité : Complétude, Unicité, Cohérence, Validité, Représentativité."),
       C("Contrôle", "Controle", "txt", desc="Description du contrôle."),
       C("Lignes en anomalie", "Nb_Anomalies", "int", summ="sum", fmt="#,##0", desc="Nombre de lignes concernées."),
       C("Lignes contrôlées", "Nb_Total", "int", summ="sum", fmt="#,##0", desc="Nombre de lignes contrôlées."),
       C("Taux", "Taux", "dec", hidden=True, desc="Lignes en anomalie / lignes contrôlées."),
       C("Gravité", "Gravite", "txt", desc="Critique, Élevée, Moyenne, Faible.", sortBy="Ordre gravité"),
       C("Commentaire", "Commentaire", "txt", desc="Impact et recommandation.")],
      [dict(name="Contrôles réalisés", expr=f"COUNTROWS({CQ})", fmt="#,##0", folder="Qualité", desc="Nombre de contrôles qualité."),
       dict(name="Contrôles critiques", expr=f"CALCULATE([Contrôles réalisés], {CQ}[Gravité] = \"Critique\")", fmt="#,##0", folder="Qualité",
            desc="Contrôles dont l'anomalie invalide l'usage d'un indicateur."),
       dict(name="Contrôles gravité élevée", expr=f"CALCULATE([Contrôles réalisés], {CQ}[Gravité] = \"Élevée\")", fmt="#,##0", folder="Qualité",
            desc="Contrôles de gravité élevée."),
       dict(name="Taux anomalie", expr=f"AVERAGE({CQ}[Taux])", fmt="0.0%", folder="Qualité", desc="Taux moyen de lignes en anomalie (par contrôle).")],
      extra_m=[('#"Ordre gravité ajouté"', 'Table.AddColumn(__PREV__, "Ordre gravité", each if [Gravite] = "Critique" then 1 else if [Gravite] = "Élevée" then 2 else if [Gravite] = "Moyenne" then 3 else 4, Int64.Type)')],
      extra_cols=[C("Ordre gravité", "Ordre gravité", "int", hidden=True, desc="Ordre de tri de la gravité.")])

# ---------------------------------------------------------------- Paramètres
table("Paramètres",
      "Paramètres de référence utilisés dans les calculs (seuils de revenu vital et de pauvreté), avec leurs sources.",
      "parametres.csv",
      [C("Paramètre", "Parametre", "txt", desc="Nom du paramètre."),
       C("Valeur", "Valeur", "dec", hidden=True, desc="Valeur numérique."),
       C("Source", "Source", "txt", desc="Source documentaire.")], [])

# ---------------------------------------------------------------- relationships / model / db
w(os.path.join(DEF, "relationships.tmdl"), "\n".join([
    "relationship 'Producteurs café to Campagne'",
    f"{T}fromColumn: 'Producteurs café'.Année",
    f"{T}toColumn: Campagne.Année",
    "",
    "relationship 'Sources de revenu to Ménages cacao'",
    f"{T}fromColumn: 'Sources de revenu cacao'.'ID ménage'",
    f"{T}toColumn: 'Ménages cacao'.'ID ménage'",
    "",
]) + "\n")

w(os.path.join(DEF, "expressions.tmdl"),
  f'/// Dossier contenant les CSV du dépôt (data). Relancer build_model.py après un déplacement du dépôt.\n'
  f'expression DossierDonnees = "{DATA_DIR}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n')

tables = ["Campagne", "Producteurs café", "Ménages cacao", "Sources de revenu cacao", "Planteurs Okapi", "Contrôles qualité", "Paramètres"]
w(os.path.join(DEF, "model.tmdl"), "\n".join([
    "model Model",
    f"{T}culture: fr-FR",
    f"{T}defaultPowerBIDataSourceVersion: powerBI_V3",
    f"{T}discourageImplicitMeasures",
    f"{T}sourceQueryCulture: fr-FR",
    f"{T}dataAccessOptions",
    f"{T*2}legacyRedirects",
    f"{T*2}returnErrorValuesAsNull",
    "",
    "annotation __PBI_TimeIntelligenceEnabled = 0",
    "",
] + [f"ref table {q(t)}" for t in tables] + ["", "ref cultureInfo fr-FR", ""]) + "\n")
w(os.path.join(DEF, "database.tmdl"), "database\n\tcompatibilityLevel: 1601\n\n")
w(os.path.join(DEF, "cultures", "fr-FR.tmdl"), "cultureInfo fr-FR\n\n")
w(os.path.join(SM, "definition.pbism"), '{\n  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",\n  "version": "4.2",\n  "settings": {}\n}\n')
w(os.path.join(SM, ".platform"), '{\n  "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",\n  "metadata": {\n    "type": "SemanticModel",\n    "displayName": "%s"\n  },\n  "config": {\n    "version": "2.0",\n    "logicalId": "%s"\n  }\n}\n' % (NAME, uuid.uuid4()))
print("Modèle écrit dans", SM)
