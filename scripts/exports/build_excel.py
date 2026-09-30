# -*- coding: utf-8 -*-
"""Génère le dashboard Excel Rikolto Café & Cacao (formules vivantes + graphiques natifs)."""
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.formula import ArrayFormula
from openpyxl.formatting.rule import FormulaRule, CellIsRule
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.comments import Comment
import aggregate

OUT = os.path.join(aggregate.LIVRABLES, "Dashboard_Rikolto_Cafe_Cacao.xlsx")
D = aggregate.build()
YEARS = sorted({c["annee"] for c in D["cafe"]})
OPS = sorted({c["op"] for c in D["cafe"]})
SECTIONS = sorted({m["Section"] for m in D["menages"]})

GREEN, COFFEE, AMBER, RED, INK, MUTED, LINE, BG = "1F5C4A", "8C5A3C", "B07A12", "B23A48", "1B2622", "56635C", "DCE1DA", "F1F3EF"
F = "Arial"
def font(sz=10, bold=False, color=INK, italic=False): return Font(name=F, size=sz, bold=bold, color=color, italic=italic)
def fill(c): return PatternFill("solid", start_color=c, end_color=c)
thin = Side(style="thin", color=LINE)
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
BLUE = Font(name=F, size=10, color="0000FF")  # saisies / données sources

wb = Workbook()
ws = wb.active; ws.title = "Dashboard"
for name in ["Séries", "Café_données", "Cacao_ménages", "Okapi", "Qualité", "Paramètres", "Lisez-moi"]:
    wb.create_sheet(name)
S, CD, CM, OK, QC, PR, LM = (wb[n] for n in ["Séries", "Café_données", "Cacao_ménages", "Okapi", "Qualité", "Paramètres", "Lisez-moi"])

def header_row(sh, row, labels, start_col=1, color=GREEN):
    for i, l in enumerate(labels):
        c = sh.cell(row=row, column=start_col + i, value=l)
        c.font = font(9, True, "FFFFFF"); c.fill = fill(color); c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True); c.border = BOX

# ============================================================ Paramètres
PR["A1"] = "Paramètres utilisés"; PR["A1"].font = font(14, True, GREEN)
header_row(PR, 3, ["Paramètre", "Valeur", "Source"])
params = [("Seuil revenu vital ménage (USD/an)", D["params"]["Seuil revenu vital ménage (USD/an)"],
           "Anker Research Institute, Living Income Reference Value RDC rurale, mise à jour 2025 (219 USD/mois, ménage de référence 6 personnes)"),
          ("Taille ménage de référence", D["params"]["Taille ménage de référence"], "Anker Research Institute, rapport 2021"),
          ("Seuil pauvreté extrême (USD/pers/jour)", D["params"]["Seuil pauvreté extrême (USD/pers/jour)"], "Banque mondiale, PPA 2017"),
          ("Seuil minimal N-1 pour calculer la rétention", 30, "Hypothèse d'analyse : en dessous, la coopérative est considérée comme nouvelle")]
for i, (a, b, c) in enumerate(params, start=4):
    PR.cell(i, 1, a).font = font(); PR.cell(i, 2, b).font = BLUE; PR.cell(i, 3, c).font = font(9, color=MUTED)
PR["B4"].number_format = "#,##0"; PR["B6"].number_format = "0.00"
PR.column_dimensions["A"].width = 44; PR.column_dimensions["B"].width = 12; PR.column_dimensions["C"].width = 110
P_LI, P_TAILLE, P_POV, P_MIN = "Paramètres!$B$4", "Paramètres!$B$5", "Paramètres!$B$6", "Paramètres!$B$7"

# ============================================================ Café_données (agrégé par campagne × coopérative)
cols = [("Campagne", "annee"), ("Coopérative", "op"), ("Producteurs (inscriptions)", "n"), ("Femmes", "femmes"), ("Jeunes 15-35", "jeunes"),
        ("Âge connu", "age_connu"), ("Superficie (ha)", "sup"), ("Production estimée (t cerise)", "prod_t"), ("CA estimé (USD)", "ca"),
        ("Marge estimée (USD)", "marge"), ("Conforme", "conforme"), ("En conversion", "conversion"), ("Non conforme", "non_conforme"),
        ("Non renseigné", "non_renseigne"), ("Nouveaux", "nouveaux"), ("Présents en N-1", "present_n1"), ("Territoire renseigné", "territoire_ok"),
        ("Carte en doublon", "doublon"), ("Personnes uniques", "uniques"), ("Année (nombre)", None)]
CD["A1"] = "Base café agrégée par campagne et coopérative (source : fact_cafe_producteurs.csv, 42 433 lignes)"; CD["A1"].font = font(11, True, GREEN)
header_row(CD, 2, [c[0] for c in cols])
rows = sorted(D["cafe"], key=lambda c: (c["annee"], c["op"]))
for r, c in enumerate(rows, start=3):
    for j, (_, k) in enumerate(cols, start=1):
        if k is None:
            CD.cell(r, j, f"=VALUE(A{r})").font = font()
        else:
            v = str(c[k]) if k == "annee" else c[k]
            cell = CD.cell(r, j, v); cell.font = BLUE
            if isinstance(v, (int, float)): cell.number_format = "#,##0" if k not in ("sup", "prod_t") else "#,##0.0"
R0, R1 = 3, 2 + len(rows)
for j in range(1, len(cols) + 1):
    CD.column_dimensions[CD.cell(2, j).column_letter].width = 14
CD.row_dimensions[2].height = 42; CD.freeze_panes = "C3"
CD.auto_filter.ref = f"A2:{CD.cell(2, len(cols)).column_letter}{R1}"
COL = {k: CD.cell(2, j).column_letter for j, (_, k) in enumerate(cols, start=1) if k}
COL["num"] = CD.cell(2, len(cols)).column_letter
def rng(k): return f"'Café_données'!${COL[k]}${R0}:${COL[k]}${R1}"
YR, OPR, NUMR = rng("annee"), rng("op"), f"'Café_données'!${COL['num']}${R0}:${COL['num']}${R1}"

# ============================================================ Dashboard : en-tête et filtres
ws.sheet_view.showGridLines = False
for col, w in zip("ABCDEFGHIJKLM", [2, 20, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 2]):
    ws.column_dimensions[col].width = w
ws.merge_cells("B1:L1"); ws["B1"] = "Rikolto RDC · Café & Cacao — Tableau de bord direction"
ws["B1"].font = font(18, True, "FFFFFF"); ws["B1"].fill = fill(GREEN); ws["B1"].alignment = Alignment(vertical="center", indent=1)
ws.merge_cells("B2:L2"); ws["B2"] = "Campagnes café 2019-2025 · enquête revenu vital cacao, mars 2024 · seuil Anker RDC rurale 2025. Analyse septembre 2026."
ws["B2"].font = font(9, color="DCEBE4"); ws["B2"].fill = fill(GREEN); ws["B2"].alignment = Alignment(vertical="top", indent=1)
ws.row_dimensions[1].height = 34; ws.row_dimensions[2].height = 20

ws["B4"] = "Campagne"; ws["B5"] = "Coopérative"
for a in ("B4", "B5"): ws[a].font = font(10, True, MUTED)
ws["C4"] = "Toutes"; ws["C5"] = "Toutes"
for a in ("C4", "C5"):
    ws[a].font = Font(name=F, size=11, bold=True, color="0000FF"); ws[a].fill = fill("FFF7D6"); ws[a].border = BOX; ws[a].alignment = Alignment(horizontal="center")
dv1 = DataValidation(type="list", formula1='"Toutes,' + ",".join(str(y) for y in YEARS) + '"', allow_blank=False)
dv2 = DataValidation(type="list", formula1='"Toutes,' + ",".join(OPS) + '"', allow_blank=False)
ws.add_data_validation(dv1); ws.add_data_validation(dv2); dv1.add("C4"); dv2.add("C5")
ws.merge_cells("D4:L5")
ws["D4"] = "Choisissez une campagne et une coopérative dans les cellules jaunes : les indicateurs café et le profil des coopératives se recalculent. Les graphiques par campagne suivent le filtre Coopérative."
ws["D4"].font = font(9, italic=True, color=MUTED); ws["D4"].alignment = Alignment(wrap_text=True, vertical="center", indent=1)

# critères (feuille Séries)
S["A1"] = "Critère campagne"; S["B1"] = '=IF(Dashboard!$C$4="Toutes","*",TEXT(Dashboard!$C$4,"0"))'
S["A2"] = "Critère coopérative"; S["B2"] = '=IF(Dashboard!$C$5="Toutes","*",Dashboard!$C$5)'
S["A3"] = "Dernière campagne sélectionnée"; S["B3"] = f'=IF(Dashboard!$C$4="Toutes",MAX({NUMR}),VALUE(Dashboard!$C$4))'
for a in ("A1", "A2", "A3"): S[a].font = font(9, True, MUTED)
YC, OC, YL = "Séries!$B$1", "Séries!$B$2", "Séries!$B$3"
def SUMSEL(k): return f"SUMIFS({rng(k)},{YR},{YC},{OPR},{OC})"

# table des personnes uniques (lignes : campagne, colonnes : coopérative)
S["A30"] = "Personnes uniques (identifiant longitudinal)"; S["A30"].font = font(10, True, GREEN)
header_row(S, 31, ["Campagne \\ OP", "Toutes"] + OPS)
urows = ["Toutes"] + [str(y) for y in YEARS]
cell_u = {(str(c["annee"]), c["op"]): c["uniques"] for c in D["cafe"]}
for i, y in enumerate(urows, start=32):
    S.cell(i, 1, y).font = font(9, True)
    for j, op in enumerate(["Toutes"] + OPS, start=2):
        if y == "Toutes" and op == "Toutes": v = D["uniques"]["total"]
        elif op == "Toutes": v = D["uniques"]["annee"][y]
        elif y == "Toutes": v = D["uniques"]["op"][op]
        else: v = cell_u.get((y, op))
        c = S.cell(i, j, v); c.font = BLUE; c.number_format = "#,##0"
U_END = 31 + len(urows)
UNIQ = (f'=INDEX(Séries!$B$32:${S.cell(31, 2 + len(OPS)).column_letter}${U_END},'
        f'MATCH(IF(Dashboard!$C$4="Toutes","Toutes",TEXT(Dashboard!$C$4,"0")),Séries!$A$32:$A${U_END},0),'
        f'MATCH(Dashboard!$C$5,Séries!$B$31:${S.cell(31, 2 + len(OPS)).column_letter}$31,0))')

def tile(row, col, label, formula, fmt, accent, note=None):
    lc = ws.cell(row, col, label); lc.font = font(8, True, MUTED); lc.fill = fill("FFFFFF"); lc.alignment = Alignment(wrap_text=True, vertical="bottom")
    lc.border = Border(top=Side(style="thick", color=accent), left=thin, right=thin)
    vc = ws.cell(row + 1, col, formula); vc.font = font(16, True, INK); vc.number_format = fmt; vc.fill = fill("FFFFFF")
    vc.alignment = Alignment(horizontal="left", vertical="center"); vc.border = Border(left=thin, right=thin)
    nc = ws.cell(row + 2, col, note); nc.font = font(7, color=MUTED, italic=True); nc.fill = fill("FFFFFF"); nc.alignment = Alignment(wrap_text=True, vertical="top")
    nc.border = Border(bottom=thin, left=thin, right=thin)

def section_title(row, text, color=GREEN):
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=12)
    c = ws.cell(row, 2, text); c.font = font(12, True, color); c.border = Border(bottom=Side(style="medium", color=color))

# ============================================================ Dashboard : KPI café
section_title(7, "Café · bénéficiaires et économie (selon les filtres)", COFFEE)
RET = (f'IF(SUMIFS({rng("n")},{NUMR},{YL}-1,{OPR},{OC})<{P_MIN},"–",'
       f'SUMIFS({rng("present_n1")},{NUMR},{YL},{OPR},{OC})/SUMIFS({rng("n")},{NUMR},{YL}-1,{OPR},{OC}))')
k1 = [("Personnes", UNIQ, "#,##0", "Identifiant longitudinal"),
      ("Inscriptions", "=" + SUMSEL("n"), "#,##0", "1 ligne = 1 producteur × campagne"),
      ("Nouveaux producteurs", "=" + SUMSEL("nouveaux"), "#,##0", None),
      ("Rétention vs N-1", "=" + RET, "0.0%", "Dernière campagne sélectionnée ; – si OP nouvelle"),
      ("Femmes", f"=IFERROR({SUMSEL('femmes')}/{SUMSEL('n')},0)", "0.0%", None),
      ("Jeunes 15-35 ans", f"=IFERROR({SUMSEL('jeunes')}/{SUMSEL('n')},0)", "0.0%", "Rapporté à tous les producteurs")]
k2 = [("Superficie déclarée (ha)", "=" + SUMSEL("sup"), "#,##0", None),
      ("Superficie moyenne (ha)", f"=IFERROR({SUMSEL('sup')}/{SUMSEL('n')},0)", "0.00", "Donnée déclarée, la plus fiable"),
      ("Certifiés conformes", f"=IFERROR({SUMSEL('conforme')}/{SUMSEL('n')},0)", "0.0%", None),
      ("Production estimée (t cerise)", "=" + SUMSEL("prod_t"), "#,##0", "ESTIMÉE par paramètres fixes"),
      ("CA estimé (M USD)", f"={SUMSEL('ca')}/1000000", "0.0", "ESTIMÉ : production × 0,55 USD/kg"),
      ("Marge estimée / producteur (USD)", f"=IFERROR({SUMSEL('marge')}/{SUMSEL('n')},0)", "#,##0", "Forfait : 60 % du CA")]
for i, (l, f_, fm, nt) in enumerate(k1): tile(8, 2 + i * 2 if False else 2 + i, l, f_, fm, COFFEE, nt)
for i, (l, f_, fm, nt) in enumerate(k2): tile(11, 2 + i, l, f_, fm, AMBER, nt)
for r in (8, 11): ws.row_dimensions[r].height = 24
for r in (9, 12): ws.row_dimensions[r].height = 26
for r in (10, 13): ws.row_dimensions[r].height = 22
# KPI qualité en bout de ligne
tile(8, 9, "Contrôles qualité", "=COUNTA(Qualité!$D$4:$D$26)", "0", RED, "Registre complet : onglet Qualité")
tile(8, 10, "Critiques", '=COUNTIF(Qualité!$H$4:$H$26,"Critique")', "0", RED, None)
tile(8, 11, "Gravité élevée", '=COUNTIF(Qualité!$H$4:$H$26,"Élevée")', "0", RED, None)
tile(11, 9, "Territoire renseigné (café)", f"=SUM({rng('territoire_ok')})/SUM({rng('n')})", "0.0%", RED, "Toutes campagnes")
tile(11, 10, "Cartes en doublon (café)", f"=SUM({rng('doublon')})/SUM({rng('n')})", "0.0%", RED, "Toutes campagnes")

# ============================================================ Cacao_ménages
mcols = [("ID ménage", "ID_Menage", "0"), ("Section", "Section", "@"), ("Sexe du chef", "Sexe", "@"), ("Taille du ménage", "Taille_Menage", "0"),
         ("Superficie cacao (ha)", "Superficie_Cacao_ha", "0.0"), ("Rendement (kg/ha)", "Rendement_kg_ha", "#,##0"), ("Prix (USD/kg)", "Prix_kg_USD", "0.00"),
         ("Revenu net total (USD/an)", "Revenu_Net_Total_USD", "#,##0"), ("Seuil ajusté à la taille (USD/an)", "Seuil_LI_Ajuste_USD", "#,##0"),
         ("Atteint seuil réf. (1/0)", "Atteint_LI_Menage_Ref", "0"), ("Atteint seuil ajusté (1/0)", "Atteint_LI_Ajuste_Taille", "0"),
         ("Revenu / pers. / jour (USD)", "Revenu_par_personne_jour", "0.00"), ("Solde revenu − dépenses (USD)", "Solde_Revenu_Depenses_USD", "#,##0"),
         ("Revenu cacao", "Rev_Cacao", "#,##0"), ("Revenu café", "Rev_Cafe", "#,##0"), ("Agroforesterie", "Rev_Agroforesterie", "#,##0"),
         ("Autres cultures vivrières", "Rev_Autres_Cultures", "#,##0"), ("Élevage", "Rev_Elevage", "#,##0"), ("Activités hors ferme", "Rev_Hors_Ferme", "#,##0"),
         ("Transferts et autres", "Rev_Transferts", "#,##0"), ("Valeur extrême (1/0)", "Flag_Outlier", "0")]
CM["A1"] = "Enquête Living Income Cacao Okapi, mars 2024 : 88 ménages valides (source : fact_cacao_menages.csv)"; CM["A1"].font = font(11, True, GREEN)
header_row(CM, 2, [c[0] for c in mcols])
for r, m in enumerate(D["menages"], start=3):
    for j, (_, k, fm) in enumerate(mcols, start=1):
        c = CM.cell(r, j, m[k]); c.font = BLUE; c.number_format = fm
M0, M1 = 3, 2 + len(D["menages"])
MC = {k: CM.cell(2, j).column_letter for j, (_, k, _) in enumerate(mcols, start=1)}
def mr(k): return f"'Cacao_ménages'!${MC[k]}${M0}:${MC[k]}${M1}"
for j in range(1, len(mcols) + 1): CM.column_dimensions[CM.cell(2, j).column_letter].width = 14
CM.row_dimensions[2].height = 42; CM.freeze_panes = "C3"; CM.auto_filter.ref = f"A2:{CM.cell(2, len(mcols)).column_letter}{M1}"
CM.cell(M1 + 2, 1, "Revenu net = somme des 7 sources. La variable « living_income » du questionnaire vaut revenu − dépenses : elle n'est pas utilisée comme revenu.").font = font(9, italic=True, color=MUTED)

# ============================================================ Dashboard : KPI cacao
section_title(15, "Cacao · revenu des ménages et écart au revenu vital (88 ménages)", GREEN)
REV, SEU = mr("Revenu_Net_Total_USD"), mr("Seuil_LI_Ajuste_USD")
tile(16, 2, "Revenu net médian (USD/an)", f"=MEDIAN({REV})", "#,##0", GREEN, None)
tile(16, 3, "Seuil revenu vital (USD/an)", f"={P_LI}", "#,##0", GREEN, "Anker 2025, ménage de 6")
tile(16, 4, "Au-dessus du seuil (réf.)", f"=AVERAGE({mr('Atteint_LI_Menage_Ref')})", "0%", GREEN, None)
tile(16, 5, "Au-dessus du seuil ajusté", f"=AVERAGE({mr('Atteint_LI_Ajuste_Taille')})", "0%", GREEN, "Seuil proportionnel à la taille")
tile(16, 6, "Écart médian au seuil ajusté (USD)", None, "#,##0", GREEN, "Ménages sous le seuil")
ws["F17"] = ArrayFormula("F17", f"=MEDIAN(IF({REV}<{SEU},{SEU}-{REV}))")
tile(16, 7, "Revenu / pers. / jour (USD)", f"=MEDIAN({mr('Revenu_par_personne_jour')})", "0.00", GREEN, "Médiane")
tile(16, 8, "Part du cacao dans le revenu", f"=SUM({mr('Rev_Cacao')})/SUM({REV})", "0%", RED, None)
tile(16, 9, "Sous 2,15 USD/pers./jour", f'=COUNTIF({mr("Revenu_par_personne_jour")},"<"&{P_POV})/COUNT({REV})', "0%", RED, None)
tile(16, 10, "Dépenses > revenu", f'=COUNTIF({mr("Solde_Revenu_Depenses_USD")},"<0")/COUNT({REV})', "0%", RED, None)
tile(16, 11, "Personnes par ménage", f"=AVERAGE({mr('Taille_Menage')})", "0.0", RED, "Contre 6 (référence)")
ws.row_dimensions[16].height = 24; ws.row_dimensions[17].height = 26; ws.row_dimensions[18].height = 22

# ============================================================ Séries (tables des graphiques)
S["A5"] = "Café par campagne (suit le filtre Coopérative)"; S["A5"].font = font(10, True, GREEN)
header_row(S, 6, ["Campagne", "Producteurs", "CKK + COOKKANZ", "COOPADE + COOKURU", "Femmes", "Jeunes 15-35", "Superficie (ha)", "Production estimée (t)", "Marge estimée / producteur", "Rétention vs N-1"])
for i, y in enumerate(YEARS, start=7):
    S.cell(i, 1, str(y)).font = font(9, True)
    ny = f'SUMIFS({rng("n")},{YR},$A{i},{OPR},{OC})'
    S.cell(i, 2, "=" + ny)
    S.cell(i, 3, f'=SUMIFS({rng("n")},{YR},$A{i},{OPR},"CKK")+SUMIFS({rng("n")},{YR},$A{i},{OPR},"COOKKANZ")')
    S.cell(i, 4, f'=SUMIFS({rng("n")},{YR},$A{i},{OPR},"COOPADE")+SUMIFS({rng("n")},{YR},$A{i},{OPR},"COOKURU")')
    S.cell(i, 5, f'=IFERROR(SUMIFS({rng("femmes")},{YR},$A{i},{OPR},{OC})/{ny},NA())')
    S.cell(i, 6, f'=IFERROR(SUMIFS({rng("jeunes")},{YR},$A{i},{OPR},{OC})/{ny},NA())')
    S.cell(i, 7, f'=SUMIFS({rng("sup")},{YR},$A{i},{OPR},{OC})')
    S.cell(i, 8, f'=SUMIFS({rng("prod_t")},{YR},$A{i},{OPR},{OC})')
    S.cell(i, 9, f'=IFERROR(SUMIFS({rng("marge")},{YR},$A{i},{OPR},{OC})/{ny},NA())')
    prev = f'SUMIFS({rng("n")},{NUMR},VALUE($A{i})-1,{OPR},{OC})'
    S.cell(i, 10, f'=IF({prev}<{P_MIN},"–",SUMIFS({rng("present_n1")},{YR},$A{i},{OPR},{OC})/{prev})')
    for j, fm in zip(range(2, 11), ["#,##0", "#,##0", "#,##0", "0.0%", "0.0%", "#,##0", "#,##0", "#,##0", "0.0%"]):
        S.cell(i, j).number_format = fm; S.cell(i, j).font = font(9)
Y_END = 6 + len(YEARS)

S["A16"] = "Cacao par section"; S["A16"].font = font(10, True, GREEN)
header_row(S, 17, ["Section", "Ménages", "Revenu net médian", "Seuil de référence", "Au-dessus seuil réf.", "Au-dessus seuil ajusté", "Taille moyenne", "Ha cacao médian", "Rendement médian (kg/ha)", "Prix médian (USD/kg)"])
SECR = mr("Section")
for i, sec in enumerate(SECTIONS + ["Ensemble"], start=18):
    S.cell(i, 1, sec).font = font(9, True)
    if sec == "Ensemble":
        S.cell(i, 2, f"=COUNT({REV})"); S.cell(i, 3, f"=MEDIAN({REV})"); S.cell(i, 4, f"={P_LI}")
        S.cell(i, 5, f"=AVERAGE({mr('Atteint_LI_Menage_Ref')})"); S.cell(i, 6, f"=AVERAGE({mr('Atteint_LI_Ajuste_Taille')})")
        S.cell(i, 7, f"=AVERAGE({mr('Taille_Menage')})"); S.cell(i, 8, f"=MEDIAN({mr('Superficie_Cacao_ha')})")
        S.cell(i, 9, f"=MEDIAN({mr('Rendement_kg_ha')})"); S.cell(i, 10, f"=MEDIAN({mr('Prix_kg_USD')})")
    else:
        S.cell(i, 2, f'=COUNTIF({SECR},$A{i})')
        for j, k in ((3, "Revenu_Net_Total_USD"), (8, "Superficie_Cacao_ha"), (9, "Rendement_kg_ha"), (10, "Prix_kg_USD")):
            ref = S.cell(i, j).coordinate
            S[ref] = ArrayFormula(ref, f"=MEDIAN(IF({SECR}=$A{i},{mr(k)}))")
        S.cell(i, 4, f"={P_LI}")
        S.cell(i, 5, f"=AVERAGEIF({SECR},$A{i},{mr('Atteint_LI_Menage_Ref')})")
        S.cell(i, 6, f"=AVERAGEIF({SECR},$A{i},{mr('Atteint_LI_Ajuste_Taille')})")
        S.cell(i, 7, f"=AVERAGEIF({SECR},$A{i},{mr('Taille_Menage')})")
    for j, fm in zip(range(2, 11), ["0", "#,##0", "#,##0", "0%", "0%", "0.0", "0.0", "#,##0", "0.00"]):
        S.cell(i, j).number_format = fm; S.cell(i, j).font = font(9, bold=(sec == "Ensemble"))
SEC_END = 17 + len(SECTIONS)

S["L5"] = "Composition du revenu net (88 ménages)"; S["L5"].font = font(10, True, GREEN)
header_row(S, 6, ["Source", "Part du revenu net"], start_col=12)
srcs = [("Cacao", "Rev_Cacao"), ("Agroforesterie", "Rev_Agroforesterie"), ("Activités hors ferme", "Rev_Hors_Ferme"), ("Transferts et autres", "Rev_Transferts"),
        ("Élevage", "Rev_Elevage"), ("Café", "Rev_Cafe"), ("Autres cultures vivrières", "Rev_Autres_Cultures")]
for i, (l, k) in enumerate(reversed(srcs), start=7):
    S.cell(i, 12, l).font = font(9, True); S.cell(i, 13, f"=SUM({mr(k)})/SUM({REV})").number_format = "0.0%"
SRC_END = 6 + len(srcs)
for col, w in zip("ABCDEFGHIJKLM", [30, 13, 15, 15, 13, 13, 13, 15, 15, 13, 3, 26, 14]): S.column_dimensions[col].width = w
S.row_dimensions[6].height = 36; S.row_dimensions[17].height = 36

# ============================================================ Dashboard : graphiques
def style_chart(ch, title, w=16.5, h=7.2):
    ch.title = title; ch.width = w; ch.height = h
    ch.title.overlay = False
    ch.legend = None  # séries nommées dans le titre : pas de chevauchement légende / axe
    for ax in (ch.x_axis, ch.y_axis): ax.delete = False
    return ch
def labels(fmt):
    dl = DataLabelList(); dl.showVal = True; dl.numFmt = fmt
    dl.showSerName = False; dl.showCatName = False; dl.showLegendKey = False; dl.showPercent = False
    return dl
c1 = BarChart(); c1.type = "col"; c1.grouping = "stacked"; c1.overlap = 100
c1.add_data(Reference(S, min_col=3, max_col=4, min_row=6, max_row=Y_END), titles_from_data=True)
c1.set_categories(Reference(S, min_col=1, min_row=7, max_row=Y_END))
c1.series[0].graphicalProperties.solidFill = COFFEE; c1.series[1].graphicalProperties.solidFill = "DDB690"
c1.y_axis.numFmt = "#,##0"; c1.y_axis.majorGridlines = None
style_chart(c1, "Producteurs par campagne : CKK + COOKKANZ (foncé), COOPADE + COOKURU (clair)")
ws.add_chart(c1, "B21")

c2 = LineChart()
c2.add_data(Reference(S, min_col=5, max_col=6, min_row=6, max_row=Y_END), titles_from_data=True)
c2.set_categories(Reference(S, min_col=1, min_row=7, max_row=Y_END))
c2.series[0].graphicalProperties.line.solidFill = COFFEE; c2.series[1].graphicalProperties.line.solidFill = GREEN
for s_ in c2.series: s_.graphicalProperties.line.width = 28000; s_.smooth = False
c2.y_axis.numFmt = "0%"; c2.y_axis.scaling.min = 0; c2.y_axis.scaling.max = 0.7
style_chart(c2, "Part des jeunes 15-35 ans (vert) et des femmes (brun)")
ws.add_chart(c2, "H21")

c3 = BarChart(); c3.type = "bar"; c3.grouping = "clustered"
c3.add_data(Reference(S, min_col=5, max_col=6, min_row=17, max_row=SEC_END), titles_from_data=True)
c3.set_categories(Reference(S, min_col=1, min_row=18, max_row=SEC_END))
c3.series[0].graphicalProperties.solidFill = "9DBFAE"; c3.series[1].graphicalProperties.solidFill = GREEN
c3.y_axis.numFmt = "0%"; c3.y_axis.scaling.min = 0; c3.y_axis.scaling.max = 1
c3.dataLabels = labels("0%")
style_chart(c3, "Ménages au-dessus du revenu vital : seuil de référence (clair), seuil ajusté (foncé)")
ws.add_chart(c3, "B37")

c4 = BarChart(); c4.type = "col"
c4.add_data(Reference(S, min_col=3, max_col=3, min_row=17, max_row=SEC_END), titles_from_data=True)
c4.set_categories(Reference(S, min_col=1, min_row=18, max_row=SEC_END))
c4.series[0].graphicalProperties.solidFill = GREEN
l4 = LineChart(); l4.add_data(Reference(S, min_col=4, max_col=4, min_row=17, max_row=SEC_END), titles_from_data=True)
l4.series[0].graphicalProperties.line.solidFill = RED; l4.series[0].graphicalProperties.line.dashStyle = "dash"
c4.dataLabels = labels("#,##0")
c4.y_axis.numFmt = "#,##0"; c4 += l4
style_chart(c4, "Revenu net médian par section (USD/an) ; pointillé : seuil de 2 628 USD")
ws.add_chart(c4, "H37")

c5 = BarChart(); c5.type = "bar"
c5.add_data(Reference(S, min_col=13, max_col=13, min_row=6, max_row=SRC_END), titles_from_data=True)
c5.set_categories(Reference(S, min_col=12, min_row=7, max_row=SRC_END))
c5.series[0].graphicalProperties.solidFill = COFFEE
c5.dataLabels = labels("0.0%"); c5.y_axis.numFmt = "0%"
c5.legend = None; style_chart(c5, "Composition du revenu net des ménages cacao")
ws.add_chart(c5, "B53")

c6 = BarChart(); c6.type = "col"
c6.add_data(Reference(S, min_col=9, max_col=9, min_row=6, max_row=Y_END), titles_from_data=True)
c6.set_categories(Reference(S, min_col=1, min_row=7, max_row=Y_END))
c6.series[0].graphicalProperties.solidFill = AMBER
c6.dataLabels = labels("#,##0"); c6.y_axis.numFmt = "#,##0"
c6.legend = None; style_chart(c6, "Marge ESTIMÉE par producteur (USD) : forfait 60 % du CA")
ws.add_chart(c6, "H53")

# ============================================================ Dashboard : profil des coopératives
section_title(69, "Profil des coopératives (selon le filtre Campagne)", COFFEE)
header_row(ws, 70, ["Coopérative", "Producteurs", "Femmes", "Jeunes 15-35", "Ha moyen", "Certifiés conformes", "Rétention vs N-1"], start_col=2, color=COFFEE)
for i, op in enumerate(OPS + ["Ensemble"], start=71):
    oc = '"*"' if op == "Ensemble" else f"$B{i}"
    def so(k): return f"SUMIFS({rng(k)},{YR},{YC},{OPR},{oc})"
    ws.cell(i, 2, op).font = font(10, True)
    ws.cell(i, 3, "=" + so("n")).number_format = "#,##0"
    ws.cell(i, 4, f"=IFERROR({so('femmes')}/{so('n')},0)").number_format = "0.0%"
    ws.cell(i, 5, f"=IFERROR({so('jeunes')}/{so('n')},0)").number_format = "0.0%"
    ws.cell(i, 6, f"=IFERROR({so('sup')}/{so('n')},0)").number_format = "0.00"
    ws.cell(i, 7, f"=IFERROR({so('conforme')}/{so('n')},0)").number_format = "0.0%"
    prev = f"SUMIFS({rng('n')},{NUMR},{YL}-1,{OPR},{oc})"
    ws.cell(i, 8, f'=IF({prev}<{P_MIN},"–",SUMIFS({rng("present_n1")},{NUMR},{YL},{OPR},{oc})/{prev})').number_format = "0.0%"
    for j in range(2, 9):
        c = ws.cell(i, j); c.border = BOX
        if j > 2: c.font = font(10, bold=(op == "Ensemble")); c.alignment = Alignment(horizontal="right")
    if op == "Ensemble":
        for j in range(2, 9): ws.cell(i, j).fill = fill("E3EEE8")
OP_END = 70 + len(OPS)
ws.conditional_formatting.add(f"D71:D{OP_END}", CellIsRule(operator="lessThan", formula=["0.15"], font=Font(name=F, color=RED, bold=True)))
ws.conditional_formatting.add(f"E71:E{OP_END}", CellIsRule(operator="lessThan", formula=["0.3"], font=Font(name=F, color=RED, bold=True)))
ws.cell(OP_END + 2, 2, "En rouge : femmes sous 15 % ou jeunes sous 30 %. Rétention = producteurs de N-1 présents en N, sur la dernière campagne sélectionnée ; « – » pour une OP nouvelle.").font = font(8, italic=True, color=MUTED)

# messages clés
section_title(OP_END + 4, "Messages clés et avertissement", GREEN)
msgs = ["1. Couverture : 12 184 producteurs café en 2025 (×3,2 depuis 2019), 25,6 % de femmes et 44,7 % de jeunes ; la hausse vient surtout de COOPADE et COOKURU (+68 % pour CKK et COOKKANZ).",
        "2. Revenu cacao : revenu net médian de 3 301 USD/an ; 59 % des ménages dépassent le seuil de référence, 40 % seulement une fois le seuil ajusté à la taille des ménages (10,3 personnes).",
        "3. Vulnérabilité : 87 % du revenu vient du cacao et 80 % des ménages vivent avec moins de 2,15 USD par personne et par jour.",
        "4. Données : production, CA et marge café sont calculés par paramètres fixes et ne mesurent pas l'impact. Collecter les ventes réelles par producteur est la priorité."]
for i, m in enumerate(msgs, start=OP_END + 5):
    ws.merge_cells(start_row=i, start_column=2, end_row=i, end_column=12)
    c = ws.cell(i, 2, m); c.font = font(10, bold=(i == OP_END + 8), color=RED if i == OP_END + 8 else INK); c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[i].height = 28
ws.cell(OP_END + 10, 2, "Sources : base consolidée Rikolto café 2019-2025 (42 433 lignes) ; enquête Living Income Cacao Okapi (88 ménages, mars 2024) ; Anker Research Institute (2025) ; Banque mondiale.").font = font(8, italic=True, color=MUTED)
ws.freeze_panes = "A6"

# ============================================================ Okapi
OK["A1"] = "Base planteurs Cacao Okapi (301 planteurs, liste 2024)"; OK["A1"].font = font(12, True, GREEN)
header_row(OK, 3, ["Section", "Planteurs", "Superficie totale (ha)", "Superficie cacao (ha)", "Ha cacao / planteur", "Part du foncier en cacao"])
for i, o in enumerate(D["okapi"], start=4):
    OK.cell(i, 1, o["section"]).font = font(10, True)
    OK.cell(i, 2, o["planteurs"]).font = BLUE; OK.cell(i, 3, o["sup_tot"]).font = BLUE; OK.cell(i, 4, o["sup_cacao"]).font = BLUE
    OK.cell(i, 5, f"=D{i}/B{i}").number_format = "0.0"; OK.cell(i, 6, f"=D{i}/C{i}").number_format = "0%"
t = 4 + len(D["okapi"])
OK.cell(t, 1, "Total").font = font(10, True)
for j, col in ((2, "B"), (3, "C"), (4, "D")): OK.cell(t, j, f"=SUM({col}4:{col}{t-1})").font = font(10, True)
OK.cell(t, 5, f"=D{t}/B{t}").number_format = "0.0"; OK.cell(t, 6, f"=D{t}/C{t}").number_format = "0%"
for col, w in zip("ABCDEF", [18, 12, 20, 20, 18, 22]): OK.column_dimensions[col].width = w
OK.cell(t + 2, 1, "Nombre de tiges estimé (≈ superficie × 1 100) pour 76 % des planteurs : à recompter lors du prochain inventaire.").font = font(9, italic=True, color=MUTED)

# ============================================================ Qualité
QC["A1"] = "Registre des contrôles qualité — base du PV de validation"; QC["A1"].font = font(12, True, RED)
QC["A2"] = "Avis proposé : validation partielle. Valider la base café comme référentiel des bénéficiaires, pas pour ses indicateurs économiques."; QC["A2"].font = font(10, True, INK)
qh = ["ID", "Base", "Dimension", "Contrôle", "Anomalies", "Total contrôlé", "Taux", "Gravité", "Impact / commentaire"]
header_row(QC, 3, qh, color=RED)
order = {"Critique": 0, "Élevée": 1, "Moyenne": 2, "Faible": 3}
for i, r in enumerate(sorted(D["qualite"], key=lambda r: (order.get(r["Gravite"], 9), r["ID"])), start=4):
    vals = [r["ID"], r["Source"], r["Dimension"], r["Controle"], r["Nb_Anomalies"], r["Nb_Total"], None, r["Gravite"], r["Commentaire"]]
    for j, v in enumerate(vals, start=1):
        c = QC.cell(i, j, v); c.font = font(9); c.border = BOX; c.alignment = Alignment(wrap_text=True, vertical="top")
    QC.cell(i, 7, f"=IFERROR(E{i}/F{i},0)").number_format = "0.0%"
    QC.cell(i, 5).number_format = "#,##0"; QC.cell(i, 6).number_format = "#,##0"
Q_END = 3 + len(D["qualite"])
for sev, bg, fg in (("Critique", RED, "FFFFFF"), ("Élevée", "F6E4E6", RED), ("Moyenne", "F5EBD6", AMBER), ("Faible", "E3EEE8", GREEN)):
    QC.conditional_formatting.add(f"H4:H{Q_END}", FormulaRule(formula=[f'$H4="{sev}"'], fill=fill(bg), font=Font(name=F, bold=True, color=fg)))
for col, w in zip("ABCDEFGHI", [5, 13, 16, 58, 11, 12, 8, 11, 60]): QC.column_dimensions[col].width = w
QC.auto_filter.ref = f"A3:I{Q_END}"; QC.freeze_panes = "A4"
QC.cell(Q_END + 2, 1, "Détail : data/qualite_controles.csv. Le taux se recalcule à partir des colonnes Anomalies et Total.").font = font(8, italic=True, color=MUTED)

# ============================================================ Lisez-moi
LM.sheet_view.showGridLines = False; LM.column_dimensions["A"].width = 3; LM.column_dimensions["B"].width = 120
lines = [("Rikolto RDC · Café & Cacao — classeur du tableau de bord", 16, True, GREEN),
         ("Version Excel du dashboard Power BI (5 pages), préparée en septembre 2026.", 10, False, MUTED), ("", 10, False, INK),
         ("Comment l'utiliser", 12, True, INK),
         ("• Onglet Dashboard : choisissez une campagne et une coopérative dans les cellules jaunes C4 et C5. Tous les indicateurs café se recalculent.", 10, False, INK),
         ("• Les graphiques par campagne suivent le filtre Coopérative. Les indicateurs cacao portent sur les 88 ménages de l'enquête.", 10, False, INK),
         ("• Texte bleu = donnée source (à ne modifier qu'en cas de correction de la base). Texte noir = formule.", 10, False, INK), ("", 10, False, INK),
         ("Onglets", 12, True, INK),
         ("• Dashboard : indicateurs clés, 6 graphiques, profil des coopératives et messages clés.", 10, False, INK),
         ("• Séries : tables calculées qui alimentent les graphiques (par campagne, par section, composition du revenu).", 10, False, INK),
         ("• Café_données : base café agrégée par campagne et coopérative (20 lignes issues des 42 433 lignes producteurs).", 10, False, INK),
         ("• Cacao_ménages : les 88 ménages de l'enquête revenu vital, une ligne par ménage.", 10, False, INK),
         ("• Okapi : liste des 301 planteurs agrégée par section. • Qualité : registre des 23 contrôles. • Paramètres : seuils et sources.", 10, False, INK), ("", 10, False, INK),
         ("Définitions et avertissements", 12, True, INK),
         ("• Jeunes = producteurs de 15 à 35 ans, rapportés à l'ensemble des producteurs (même définition que le rapport et Power BI).", 10, False, INK),
         ("• Rétention = producteurs de N-1 présents en N, calculée sur la dernière campagne sélectionnée ; non calculée si la coopérative avait moins de 30 producteurs en N-1.", 10, False, INK),
         ("• Seuil ajusté = seuil Anker proportionnel à la taille réelle du ménage (438 USD par personne et par an).", 10, False, INK),
         ("• Production, chiffre d'affaires et marge café sont ESTIMÉS par paramètres fixes (densité, rendement par pied, prix unique de 0,55 USD/kg, marge forfaitaire de 60 %). Ils ne mesurent pas un revenu réel.", 10, True, RED),
         ("• Enquête cacao : 88 ménages dont 6 dirigés par des femmes ; résultats indicatifs, à ne pas extrapoler par sous-groupe.", 10, False, INK)]
for i, (txt, sz, b, colr) in enumerate(lines, start=2):
    c = LM.cell(i, 2, txt); c.font = font(sz, b, colr); c.alignment = Alignment(wrap_text=True, vertical="top")

wb.move_sheet("Lisez-moi", offset=-(len(wb.sheetnames) - 1))
wb.active = 1
for sh in wb.worksheets:
    sh.sheet_properties.tabColor = {"Dashboard": GREEN, "Lisez-moi": MUTED, "Qualité": RED}.get(sh.title, LINE)
wb.save(OUT)
print(OUT)
