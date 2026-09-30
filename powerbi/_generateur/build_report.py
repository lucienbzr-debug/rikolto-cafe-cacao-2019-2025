# -*- coding: utf-8 -*-
"""Génère le rapport PBIR (5 pages) du tableau de bord Rikolto Café & Cacao."""
import os, json, uuid, shutil, hashlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NAME = "Rikolto_Cafe_Cacao"
RP = os.path.join(ROOT, f"{NAME}.Report")
TEMPLATE_BASE_THEME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Fluent2-CY26SU08.json")  # thème de base Microsoft Fluent 2

VC_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json"
PAGE_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"
THEME_NAME = "RikoltoCafeCacao"
THEME_FILE = f"{THEME_NAME}-{uuid.uuid4().hex[:8]}.json"

# Palette (Rikolto : vert foncé / café / ambre / ardoise)
INK, MUTED, BG, LINE = "#1E2A26", "#5B6560", "#F6F4EF", "#E3E0D8"
GREEN, COFFEE, AMBER, SLATE, RED, SAGE = "#1F5C4A", "#8C5A3C", "#C98A1E", "#4A6FA5", "#B23A48", "#7A9E7E"

def wjson(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def vid(*parts):
    return hashlib.md5("|".join(parts).encode()).hexdigest()[:20]

# ---------------------------------------------------------------- expressions
def L(v):
    return {"expr": {"Literal": {"Value": v}}}
def S(s):
    return L("'" + s.replace("'", "''") + "'")
def B(b):
    return L("true" if b else "false")
def D(n):
    return L(f"{n}D")
def Lg(n):
    return L(f"{n}L")
def COL(hex_):
    return {"solid": {"color": S(hex_)}}

def col(t, c):
    return {"Column": {"Expression": {"SourceRef": {"Entity": t}}, "Property": c}}
def mea(t, m):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": t}}, "Property": m}}
def proj(field, display=None):
    k = "Column" if "Column" in field else "Measure"
    t = field[k]["Expression"]["SourceRef"]["Entity"]; p = field[k]["Property"]
    d = {"field": field, "queryRef": f"{t}.{p}", "nativeQueryRef": p}
    if display:
        d["displayName"] = display
    return d

def vco(title=None, subtitle=None, bg=True, border=True, pad=8):
    o = {"padding": [{"properties": {"top": D(pad), "bottom": D(pad), "left": D(pad + 2), "right": D(pad + 2)}}]}
    if title:
        o["title"] = [{"properties": {"show": B(True), "text": S(title), "fontSize": D(12), "bold": B(True), "fontColor": COL(INK)}}]
    else:
        o["title"] = [{"properties": {"show": B(False)}}]
    if subtitle:
        o["subTitle"] = [{"properties": {"show": B(True), "text": S(subtitle), "fontSize": D(9), "fontColor": COL(MUTED)}}]
    o["background"] = [{"properties": {"show": B(bg), "color": COL("#FFFFFF"), "transparency": D(0)}}]
    o["border"] = [{"properties": {"show": B(border), "color": COL(LINE), "radius": D(8)}}]
    o["visualHeader"] = [{"properties": {"show": B(False)}}]
    return o

class Page:
    def __init__(self, key, display):
        self.name = vid("page", key); self.display = display; self.visuals = []; self.z = 1000
    def add(self, key, x, y, w, h, visual):
        self.z += 1000
        self.visuals.append({"$schema": VC_SCHEMA, "name": vid(self.name, key),
                             "position": {"x": x, "y": y, "z": self.z, "height": h, "width": w, "tabOrder": self.z},
                             "visual": visual})

# ---------------------------------------------------------------- visual builders
def textbox(paras, bg=False, border=False, pad=0, bgcolor="#FFFFFF"):
    """paras: list of list of (text, size, color, bold)"""
    P = []
    for runs in paras:
        tr = []
        for (txt, size, color, bold) in runs:
            tr.append({"value": txt, "textStyle": {"fontFamily": "Segoe UI Semibold" if bold else "Segoe UI", "fontSize": f"{size}pt", "color": color}})
        P.append({"textRuns": tr, "horizontalTextAlignment": "left"})
    v = {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": P}}]},
         "visualContainerObjects": {
             "background": [{"properties": {"show": B(bg), "color": COL(bgcolor), "transparency": D(0)}}],
             "border": [{"properties": {"show": B(border), "color": COL(LINE), "radius": D(8)}}],
             "padding": [{"properties": {"top": D(pad), "bottom": D(pad), "left": D(pad + 4), "right": D(pad + 4)}}],
             "visualHeader": [{"properties": {"show": B(False)}}]}}
    return v

def shape(fill):
    return {"visualType": "shape",
            "objects": {"shape": [{"properties": {"tileShape": S("rectangle")}}],
                        "fill": [{"properties": {"show": B(True), "fillColor": COL(fill), "transparency": D(0)}, "selector": {"id": "default"}}],
                        "outline": [{"properties": {"show": B(False)}, "selector": {"id": "default"}}]},
            "visualContainerObjects": {"background": [{"properties": {"show": B(False)}}],
                                       "border": [{"properties": {"show": B(False)}}],
                                       "padding": [{"properties": {"top": D(0), "bottom": D(0), "left": D(0), "right": D(0)}}],
                                       "visualHeader": [{"properties": {"show": B(False)}}]}}

def cards(items, accent=GREEN, value_size=20, millions=()):
    """items: list of (field, label); millions: fields shown in millions (1 decimal)"""
    vals = [{"properties": {"fontSize": D(value_size), "fontColor": COL(INK), "bold": B(True), "labelDisplayUnits": D(1)}, "selector": {"id": "default"}}]
    for f in millions:
        vals.append({"properties": {"labelDisplayUnits": D(1000000), "labelPrecision": Lg(1)}, "selector": {"metadata": proj(f)["queryRef"]}})
    return {"visualType": "cardVisual",
            "query": {"queryState": {"Data": {"projections": [proj(f, lab) for f, lab in items]}}},
            "objects": {
                "value": vals,
                "label": [{"properties": {"show": B(True), "fontSize": D(10), "fontColor": COL(MUTED)}, "selector": {"id": "default"}}],
                "outline": [{"properties": {"show": B(False)}, "selector": {"id": "default"}}],
                "padding": [{"properties": {"paddingUniform": Lg(6)}, "selector": {"id": "default"}}],
                "layout": [{"properties": {"paddingUniform": Lg(4), "style": S("Table"), "customizeLines": B(True),
                                           "gridlineWidth": D(1), "gridlineColor": COL(LINE), "gridlineTransparency": D(0), "gridlineStyle": S("solid")},
                            "selector": {"id": "default"}}],
                "accentBar": [{"properties": {"show": B(True), "position": S("Top"), "width": D(3), "color": COL(accent)}, "selector": {"id": "default"}}],
            },
            "visualContainerObjects": vco(pad=4)}

def chart(vtype, cat, ys, title, subtitle=None, series=None, sort_by=None, sort_dir="Descending",
          colors=None, labels=True, legend=None, label_fmt=None, y2=None):
    qs = {"Category": {"projections": [proj(cat)]}, "Y": {"projections": [proj(y) for y in ys]}}
    if series:
        qs["Series"] = {"projections": [proj(series)]}
    if y2:
        qs["Y2"] = {"projections": [proj(y) for y in y2]}
    q = {"queryState": qs}
    if sort_by is not None:
        q["sortDefinition"] = {"sort": [{"field": sort_by, "direction": sort_dir}], "isDefaultSort": False}
    obj = {}
    if labels:
        lp = {"show": B(True), "fontSize": D(9), "color": COL(INK)}
        if label_fmt:
            lp["labelDisplayUnits"] = S(label_fmt)
        obj["labels"] = [{"properties": lp}]
    if legend is not None:
        obj["legend"] = [{"properties": {"show": B(legend), "position": S("Top")}}]
    if colors:
        if len(ys) == 1 and not series and not y2:
            obj["dataPoint"] = [{"properties": {"defaultColor": COL(colors[0])}}]
        else:
            fields = ys + (y2 or [])
            obj["dataPoint"] = [{"properties": {"fill": COL(c)}, "selector": {"metadata": proj(f)["queryRef"]}} for f, c in zip(fields, colors)]
    obj["valueAxis"] = [{"properties": {"showAxisTitle": B(False), "gridlineShow": B(False) if vtype.startswith("clusteredBar") else B(True)}}]
    obj["categoryAxis"] = [{"properties": {"showAxisTitle": B(False)}}]
    v = {"visualType": vtype, "query": q, "objects": obj, "visualContainerObjects": vco(title, subtitle)}
    return v

def line(cat, ys, title, subtitle=None, colors=None):
    v = chart("lineChart", cat, ys, title, subtitle, colors=None, legend=len(ys) > 1)
    v["objects"]["lineStyles"] = [{"properties": {"strokeWidth": D(3), "showMarker": B(True), "markerSize": D(5)}}]
    if colors:
        v["objects"]["dataPoint"] = [{"properties": {"fill": COL(c)}, "selector": {"metadata": proj(f)["queryRef"]}} for f, c in zip(ys, colors)]
    return v

def donut(cat, y, title, subtitle=None):
    return {"visualType": "donutChart",
            "query": {"queryState": {"Category": {"projections": [proj(cat)]}, "Y": {"projections": [proj(y)]}}},
            "objects": {"legend": [{"properties": {"show": B(True), "position": S("Bottom")}}],
                        "labels": [{"properties": {"show": B(True), "labelStyle": S("Percent of total")}}]},
            "visualContainerObjects": vco(title, subtitle)}

def table_(fields, title, subtitle=None, sort_by=None, sort_dir="Ascending"):
    q = {"queryState": {"Values": {"projections": [proj(f, d) for f, d in fields]}}}
    if sort_by is not None:
        q["sortDefinition"] = {"sort": [{"field": sort_by, "direction": sort_dir}], "isDefaultSort": False}
    return {"visualType": "tableEx", "query": q,
            "objects": {"columnHeaders": [{"properties": {"columnAdjustment": S("growToFit"), "autoSizeColumnWidth": B(True), "wordWrap": B(True),
                                                          "bold": B(True), "fontColor": COL("#FFFFFF"), "backColor": COL(GREEN), "fontSize": D(9)}}],
                        "values": [{"properties": {"fontSize": D(9), "wordWrap": B(True), "backColorPrimary": COL("#FFFFFF"), "backColorSecondary": COL("#F7F6F2")}}],
                        "grid": [{"properties": {"gridHorizontal": B(True), "gridHorizontalColor": COL(LINE)}}],
                        "total": [{"properties": {"totals": B(False)}}]},
            "visualContainerObjects": {**vco(title, subtitle), "stylePreset": [{"properties": {"name": S("None")}}]}}

def matrix(rows, cols, vals, title, subtitle=None):
    qs = {"Rows": {"projections": [proj(r) for r in rows]}, "Values": {"projections": [proj(v, d) for v, d in vals]}}
    if cols:
        qs["Columns"] = {"projections": [proj(c) for c in cols]}
    return {"visualType": "pivotTable", "query": {"queryState": qs},
            "objects": {"columnHeaders": [{"properties": {"columnAdjustment": S("growToFit"), "autoSizeColumnWidth": B(True), "wordWrap": B(True),
                                                          "bold": B(True), "fontColor": COL("#FFFFFF"), "backColor": COL(GREEN), "fontSize": D(9)}}],
                        "rowHeaders": [{"properties": {"fontSize": D(9), "bold": B(True)}}],
                        "values": [{"properties": {"fontSize": D(9), "backColorPrimary": COL("#FFFFFF"), "backColorSecondary": COL("#F7F6F2")}}]},
            "visualContainerObjects": {**vco(title, subtitle), "stylePreset": [{"properties": {"name": S("None")}}]}}

def slicer(field, header, sync=None):
    v = {"visualType": "slicer",
         "query": {"queryState": {"Values": {"projections": [proj(field)]}}},
         "objects": {"data": [{"properties": {"mode": S("Dropdown")}}],
                     "header": [{"properties": {"show": B(True), "text": S(header)}}]},
         "visualContainerObjects": {"background": [{"properties": {"show": B(True), "color": COL("#FFFFFF"), "transparency": D(0)}}],
                                    "border": [{"properties": {"show": B(True), "color": COL(LINE), "radius": D(8)}}],
                                    "padding": [{"properties": {"top": D(8), "bottom": D(8), "left": D(8), "right": D(8)}}],
                                    "visualHeader": [{"properties": {"show": B(False)}}]}}
    if sync:
        v["syncGroup"] = {"groupName": sync, "fieldChanges": True, "filterChanges": True}
    return v

# ---------------------------------------------------------------- fields
PC, MC, SR, OK, CQ, CA = "Producteurs café", "Ménages cacao", "Sources de revenu cacao", "Planteurs Okapi", "Contrôles qualité", "Campagne"
m = lambda t, n: mea(t, n)
c = lambda t, n: col(t, n)
YEAR = c(CA, "Libellé campagne")

def header(p, title, sub):
    p.add("band", 0, 0, 1280, 64, shape(GREEN))
    p.add("title", 20, 6, 900, 54, textbox([[(title, 18, "#FFFFFF", True)], [(sub, 10, "#D9E6E0", False)]]))
    p.add("brand", 1000, 14, 260, 40, textbox([[("RIKOLTO RDC · Café & Cacao", 10, "#FFFFFF", True)], [("Données 2019-2025 · Analyse sept. 2026", 8, "#D9E6E0", False)]]))

def footnote(p, txt, y=694):
    p.add("foot", 20, y, 1240, 24, textbox([[(txt, 8, MUTED, False)]]))

pages = []

# ===== Page 1 : Synthèse
p = Page("synthese", "1. Synthèse direction"); pages.append(p)
header(p, "Synthèse pour la direction", "Chiffres clés café (campagne 2025) et cacao (enquête revenu vital 2024)")
KPI_CAFE_KEY = "kpi_cafe"
p.add("kpi_cafe", 20, 76, 760, 112, cards([
    (m(PC, "Producteurs"), "Producteurs café 2025"), (m(PC, "% femmes"), "Femmes"), (m(PC, "% jeunes (15-35 ans)"), "Jeunes 15-35 ans"),
    (m(PC, "Superficie totale (ha)"), "Superficie (ha)"), (m(PC, "% certifiés conformes"), "Certifiés conformes")], accent=COFFEE))
p.add("kpi_cacao", 792, 76, 468, 112, cards([
    (m(MC, "Ménages enquêtés"), "Ménages cacao enquêtés"), (m(MC, "Revenu net médian (USD/an)"), "Revenu net médian (USD/an)"),
    (m(MC, "% au-dessus du revenu vital"), "Au-dessus du revenu vital")], accent=GREEN))
p.add("evol", 20, 200, 620, 290, chart("clusteredColumnChart", YEAR, [m(PC, "Producteurs")],
      "Producteurs café enregistrés par campagne", "Doublement en 2024-2025 lié à l'intégration de COOPADE puis COOKURU", colors=[COFFEE], legend=False))
p.add("li_section", 652, 200, 608, 290, chart("clusteredBarChart", c(MC, "Section"), [m(MC, "% au-dessus du revenu vital"), m(MC, "% au-dessus du revenu vital (ajusté taille)")],
      "Ménages cacao atteignant le revenu vital, par section", "Seuil Anker RDC rurale 2025 : 2 628 USD/an (ménage de 6) · vision ajustée à la taille réelle",
      sort_by=m(MC, "% au-dessus du revenu vital"), colors=[GREEN, AMBER], legend=True))
p.add("msg", 20, 502, 820, 186, textbox([
    [("Messages clés", 12, INK, True)],
    [("① Couverture : 12 184 producteurs café en 2025 (×3,2 depuis 2019), 25,6 % de femmes et 44,7 % de jeunes. La hausse vient surtout de 2 nouvelles coopératives.", 9, INK, False)],
    [("② Revenu cacao : revenu net médian de 3 300 USD/an ; 59 % des ménages dépassent le seuil de référence, mais seulement 40 % une fois le seuil ajusté à la taille réelle des ménages (10 personnes en moyenne).", 9, INK, False)],
    [("③ Vulnérabilité : 87 % du revenu vient du cacao, et 80 % des ménages vivent avec moins de 2,15 USD par personne et par jour.", 9, INK, False)],
    [("④ Données : les revenus, marges et productions café sont calculés par paramètres fixes et ne mesurent pas l'impact. Collecter des données réelles est la priorité n°1.", 9, RED, True)],
], bg=True, border=True, pad=10))
p.add("dq", 852, 502, 408, 186, cards([
    (m(CQ, "Contrôles réalisés"), "Contrôles qualité"), (m(CQ, "Contrôles critiques"), "Critiques"), (m(CQ, "Contrôles gravité élevée"), "Gravité élevée")],
    accent=RED, value_size=22))
footnote(p, "Sources : base consolidée Rikolto café 2019-2025 (42 433 lignes) ; enquête Living Income Cacao Okapi (88 ménages, mars 2024) ; Anker Research Institute (2025). Cartes café : campagne 2025.")

# ===== Page 2 : Café bénéficiaires & inclusion
p2 = Page("cafe_benef", "2. Café – Bénéficiaires & inclusion"); pages.append(p2)
header(p2, "Café : bénéficiaires et inclusion", "Effectifs, genre, jeunesse, fidélisation et certification par coopérative")
p2.add("s_year", 20, 76, 200, 80, slicer(YEAR, "Campagne", "sync_campagne"))
p2.add("s_coop", 232, 76, 200, 80, slicer(c(PC, "Coopérative"), "Coopérative", "sync_coop"))
p2.add("kpi", 444, 76, 816, 104, cards([
    (m(PC, "Producteurs uniques"), "Personnes"), (m(PC, "Nouveaux producteurs"), "Nouveaux"), (m(PC, "Taux de rétention"), "Rétention"),
    (m(PC, "% femmes"), "Femmes"), (m(PC, "% jeunes (15-35 ans)"), "Jeunes 15-35 ans")], accent=COFFEE))
p2.add("coop_year", 20, 192, 620, 250, chart("clusteredColumnChart", YEAR, [m(PC, "Producteurs")], "Producteurs par campagne et coopérative",
       "Empilement des coopératives : l'essentiel de la croissance vient de COOPADE (2024) et COOKURU (2025)", series=c(PC, "Coopérative"), legend=True, labels=False))
p2.add("incl", 652, 192, 608, 250, line(YEAR, [m(PC, "% femmes"), m(PC, "% jeunes (15-35 ans)")], "Inclusion : part des femmes et des jeunes",
       "Part des jeunes en baisse de 61 % (2019) à 32 % (2023) puis en reprise avec les nouvelles OP", colors=[COFFEE, GREEN]))
p2.add("coop_tab", 20, 454, 820, 234, matrix([c(PC, "Coopérative")], None, [
    (m(PC, "Producteurs"), "Producteurs"), (m(PC, "% femmes"), "% femmes"), (m(PC, "% jeunes (15-35 ans)"), "% jeunes"),
    (m(PC, "Superficie moyenne (ha)"), "Superficie moy. (ha)"), (m(PC, "% certifiés conformes"), "% conformes"), (m(PC, "Taux de rétention"), "Rétention")],
    "Profil des coopératives", "Selon la campagne sélectionnée"))
p2.add("certif", 852, 454, 408, 234, donut(c(PC, "Certification"), m(PC, "Producteurs"), "Statut de certification bio / fairtrade", "COOKURU : 100 % en conversion en 2025"))
footnote(p2, "Rétention = producteurs de N-1 présents en N, sur la dernière campagne sélectionnée (vide pour une OP nouvelle). 3 216 producteurs sont présents sur les 7 campagnes.")

# ===== Page 3 : Café production & économie
p3 = Page("cafe_eco", "3. Café – Production & économie"); pages.append(p3)
header(p3, "Café : production et économie (estimations)", "À lire avec prudence : production, CA et marge sont calculés par paramètres, pas mesurés")
p3.add("s_year", 20, 76, 200, 80, slicer(YEAR, "Campagne", "sync_campagne"))
p3.add("s_coop", 232, 76, 200, 80, slicer(c(PC, "Coopérative"), "Coopérative", "sync_coop"))
p3.add("kpi", 444, 76, 816, 104, cards([
    (m(PC, "Superficie totale (ha)"), "Superficie (ha)"), (m(PC, "Superficie moyenne (ha)"), "Superficie moy. (ha)"),
    (m(PC, "Production estimée (t cerise)"), "Production estimée (t cerise)"), (m(PC, "CA estimé (USD)"), "CA estimé (USD)"),
    (m(PC, "Marge estimée par producteur (USD)"), "Marge estimée / producteur (USD)")], accent=AMBER, millions=[m(PC, "CA estimé (USD)")]))
p3.add("prod", 20, 192, 620, 250, chart("lineClusteredColumnComboChart", YEAR, [m(PC, "Superficie totale (ha)")],
       "Superficie déclarée et production estimée", "La production estimée augmente 2,4× plus vite que la superficie : effet des paramètres de rendement",
       y2=[m(PC, "Production estimée (t cerise)")], colors=[SAGE, COFFEE], legend=True, labels=False))
p3.add("marge", 652, 192, 608, 250, chart("clusteredColumnChart", YEAR, [m(PC, "Marge estimée par producteur (USD)")],
       "Marge estimée par producteur (USD)", "Marge = 60 % du CA pour 100 % des lignes : indicateur forfaitaire", colors=[AMBER], legend=False))
p3.add("warn", 20, 454, 500, 234, textbox([
    [("⚠ Pourquoi ces chiffres ne mesurent pas l'impact", 12, RED, True)],
    [("• Production = superficie × densité × rendement par pied. Les deux paramètres changent chaque année (1 000 → 1 620 pieds/ha ; 1,5 → 2,5 kg/pied).", 9, INK, False)],
    [("• Chiffre d'affaires = production × 0,55 USD/kg, un prix unique sur 7 ans.", 9, INK, False)],
    [("• Coût = 40 % et marge = 60 % du CA pour 100 % des lignes.", 9, INK, False)],
    [("• La colonne « Prix unitaire » reprend en réalité le taux de transformation cerise → parche.", 9, INK, False)],
    [("➜ Seule la superficie (0,55 ha en moyenne, stable) est une donnée déclarée. Recommandation : collecter les ventes réelles par producteur.", 9, GREEN, True)],
], bg=True, border=True, pad=10))
p3.add("tab", 532, 454, 728, 234, matrix([c(PC, "Coopérative")], [YEAR], [(m(PC, "Superficie totale (ha)"), "Superficie (ha)")],
       "Superficie déclarée (ha) par coopérative et campagne", "Donnée déclarée : l'indicateur le plus fiable du volet économique"))
footnote(p3, "Paramètres observés dans la base : densité, rendement/pied et taux cerise → parche sont constants pour une campagne donnée.")

# ===== Page 4 : Cacao revenu vital
p4 = Page("cacao_li", "4. Cacao – Revenu vital"); pages.append(p4)
header(p4, "Cacao : revenu des ménages et écart au revenu vital", "Enquête Living Income, 88 ménages Cacao Okapi, mars 2024 · Benchmark Anker RDC rurale 2025")
p4.add("s_sec", 20, 76, 200, 80, slicer(c(MC, "Section"), "Section"))
p4.add("kpi", 232, 76, 1028, 104, cards([
    (m(MC, "Revenu net médian (USD/an)"), "Revenu net médian (USD/an)"), (m(MC, "Seuil revenu vital (USD/an)"), "Seuil revenu vital (USD/an)"),
    (m(MC, "% au-dessus du revenu vital"), "Au-dessus du seuil (réf. 6 pers.)"), (m(MC, "% au-dessus du revenu vital (ajusté taille)"), "Au-dessus du seuil (ajusté)"),
    (m(MC, "Écart médian au revenu vital ajusté (USD)"), "Écart médian au seuil ajusté (USD)"), (m(MC, "Revenu médian par personne et par jour (USD)"), "USD / personne / jour")], accent=GREEN, value_size=18))
p4.add("rev_sec", 20, 192, 410, 250, chart("clusteredBarChart", c(MC, "Section"), [m(MC, "Revenu net médian (USD/an)")],
       "Revenu net médian par section (USD/an)", "À comparer au seuil de 2 628 USD/an", sort_by=m(MC, "Revenu net médian (USD/an)"), colors=[GREEN], legend=False))
p4.add("src", 442, 192, 410, 250, chart("clusteredBarChart", c(SR, "Source"), [m(SR, "Part de la source")],
       "Composition du revenu net", "Forte dépendance au cacao : un choc de prix touche tout le revenu", sort_by=m(SR, "Part de la source"), colors=[COFFEE], legend=False))
p4.add("prod", 864, 192, 396, 250, matrix([c(MC, "Section")], None, [
    (m(MC, "Ménages enquêtés"), "Ménages"), (m(MC, "Taille moyenne du ménage"), "Taille"), (m(MC, "Superficie cacao médiane (ha)"), "Ha cacao"),
    (m(MC, "Rendement médian (kg/ha)"), "kg/ha"), (m(MC, "Prix médian (USD/kg)"), "USD/kg")], "Leviers : rendement, prix, taille du ménage",
    "Mayuano : rendement ×2 mais prix ÷2"))
p4.add("vuln", 20, 454, 620, 234, cards([
    (m(MC, "Part du cacao dans le revenu"), "Part du cacao dans le revenu"), (m(MC, "% sous 2,15 USD par personne et par jour"), "Sous 2,15 USD/pers/jour"),
    (m(MC, "% ménages dépenses supérieures au revenu"), "Dépenses > revenu"), (m(MC, "Taille moyenne du ménage"), "Personnes par ménage")], accent=RED, value_size=24))
p4.add("okapi", 652, 454, 608, 234, matrix([c(OK, "Section")], None, [
    (m(OK, "Planteurs Okapi"), "Planteurs"), (m(OK, "Superficie cacao Okapi (ha)"), "Ha cacao"), (m(OK, "Superficie cacao moyenne Okapi (ha)"), "Ha cacao / planteur"),
    (m(OK, "Part du foncier en cacao"), "% foncier en cacao")], "Base planteurs Cacao Okapi (301 planteurs)", "Liste officielle des planteurs par section"))
footnote(p4, "Revenu net = cacao + café + agroforesterie + autres cultures + élevage + hors ferme + transferts. La variable « living_income » du questionnaire (revenu − dépenses) n'est pas un revenu. Échantillon indicatif (6 femmes).")

# ===== Page 5 : Qualité des données
p5 = Page("qualite", "5. Qualité des données"); pages.append(p5)
header(p5, "Qualité des données : diagnostic pour la validation de la base", "23 contrôles de complétude, unicité, cohérence, validité et représentativité")
p5.add("s_base", 20, 76, 200, 80, slicer(c(CQ, "Base"), "Base"))
p5.add("s_grav", 232, 76, 200, 80, slicer(c(CQ, "Gravité"), "Gravité"))
p5.add("kpi", 444, 76, 816, 104, cards([
    (m(CQ, "Contrôles réalisés"), "Contrôles"), (m(CQ, "Contrôles critiques"), "Critiques"), (m(CQ, "Contrôles gravité élevée"), "Gravité élevée"),
    (m(PC, "% territoire renseigné"), "Territoire renseigné (café)"), (m(PC, "% cartes en doublon"), "Cartes en doublon (café)")], accent=RED))
p5.add("tab", 20, 192, 820, 496, table_([
    (c(CQ, "Gravité"), "Gravité"), (c(CQ, "Base"), "Base"), (c(CQ, "Contrôle"), "Contrôle"),
    (c(CQ, "Lignes en anomalie"), "Anomalies"), (m(CQ, "Taux anomalie"), "Taux"), (c(CQ, "Commentaire"), "Impact")],
    "Registre des contrôles qualité", "Trié par gravité", sort_by=c(CQ, "Gravité")))
p5.add("dim", 852, 192, 408, 240, chart("clusteredBarChart", c(CQ, "Dimension"), [m(CQ, "Contrôles réalisés")], "Contrôles par dimension qualité",
       None, sort_by=m(CQ, "Contrôles réalisés"), colors=[SLATE], legend=False))
p5.add("reco", 852, 444, 408, 244, textbox([
    [("Pour le PV de validation", 12, INK, True)],
    [("1. Ne pas valider en l'état les indicateurs économiques café (production, CA, marge).", 9, INK, False)],
    [("2. Compléter territoire, collectivité et certification (2022, 2024).", 9, INK, False)],
    [("3. Dédoublonner les 2 099 lignes à carte partagée.", 9, INK, False)],
    [("4. Renommer « living_income » en « solde revenu − dépenses ».", 9, INK, False)],
    [("5. Valider la base comme référentiel des bénéficiaires (effectifs, genre, âge, OP).", 9, GREEN, True)],
], bg=True, border=True, pad=10))
footnote(p5, "Détail complet : data/qualite_controles.csv. Les indicateurs de complétude café se calculent sur la campagne sélectionnée (toutes par défaut).")

# ---------------------------------------------------------------- page filter: synthèse = 2025
def year_filter(year):
    return {"filters": [{"name": "Filter" + hashlib.md5(b"f2025").hexdigest()[:24],
                         "field": col(CA, "Libellé campagne"), "type": "Categorical",
                         "filter": {"Version": 2, "From": [{"Name": "c", "Entity": CA, "Type": 0}],
                                    "Where": [{"Condition": {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "c"}}, "Property": "Libellé campagne"}}],
                                                                    "Values": [[{"Literal": {"Value": f"'{year}'"}}]]}}}]},
                         "howCreated": "User"}]}

# ---------------------------------------------------------------- write report
if os.path.exists(os.path.join(RP, "definition")):
    shutil.rmtree(os.path.join(RP, "definition"))
for sub in ["StaticResources/RegisteredResources"]:
    d = os.path.join(RP, sub)
    if os.path.exists(d):
        shutil.rmtree(d)
os.makedirs(os.path.join(RP, "StaticResources", "SharedResources", "BaseThemes"), exist_ok=True)
shutil.copy(TEMPLATE_BASE_THEME, os.path.join(RP, "StaticResources", "SharedResources", "BaseThemes", "Fluent2-CY26SU08.json"))

theme = {
    "name": THEME_FILE,
    "dataColors": [GREEN, COFFEE, AMBER, SLATE, SAGE, RED, "#6B6F76", "#D6B68A"],
    "foreground": INK, "background": "#FFFFFF", "tableAccent": GREEN,
    "good": GREEN, "neutral": AMBER, "bad": RED,
    "textClasses": {
        "callout": {"fontSize": 20, "fontFace": "Segoe UI Semibold", "color": INK},
        "title": {"fontSize": 12, "fontFace": "Segoe UI Semibold", "color": INK},
        "header": {"fontSize": 11, "fontFace": "Segoe UI Semibold", "color": INK},
        "label": {"fontSize": 10, "fontFace": "Segoe UI", "color": MUTED},
    },
    "visualStyles": {"*": {"*": {
        "border": [{"show": True, "color": {"solid": {"color": LINE}}, "radius": 8}],
        "padding": [{"top": 8, "bottom": 8, "left": 10, "right": 10}],
        "visualHeader": [{"show": False}],
    }}},
}
wjson(os.path.join(RP, "StaticResources", "RegisteredResources", THEME_FILE), theme)

rv = {"visual": "2.12.0", "report": "3.4.0", "page": "2.3.1"}
wjson(os.path.join(RP, "definition", "report.json"), {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json",
    "themeCollection": {"baseTheme": {"name": "Fluent2-CY26SU08", "reportVersionAtImport": rv, "type": "SharedResources"},
                        "customTheme": {"name": THEME_FILE, "reportVersionAtImport": rv, "type": "RegisteredResources"}},
    "objects": {"section": [{"properties": {"verticalAlignment": S("Top")}}],
                "outspacePane": [{"properties": {"visible": B(True), "expanded": B(False)}}]},
    "resourcePackages": [
        {"name": "SharedResources", "type": "SharedResources", "items": [{"name": "Fluent2-CY26SU08", "path": "BaseThemes/Fluent2-CY26SU08.json", "type": "BaseTheme"}]},
        {"name": "RegisteredResources", "type": "RegisteredResources", "items": [{"name": THEME_FILE, "path": THEME_FILE, "type": "CustomTheme"}]}],
    "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized", "defaultDrillFilterOtherVisuals": True,
                 "allowChangeFilterTypes": True, "useEnhancedTooltips": True, "useDefaultAggregateDisplayName": True},
})
wjson(os.path.join(RP, "definition", "version.json"), {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
wjson(os.path.join(RP, "definition", "pages", "pages.json"), {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
    "pageOrder": [pg.name for pg in pages], "activePageName": pages[0].name})
for pg in pages:
    pj = {"$schema": PAGE_SCHEMA, "name": pg.name, "displayName": pg.display, "displayOption": "FitToPage", "height": 720, "width": 1280,
          "objects": {"background": [{"properties": {"color": COL(BG), "transparency": D(0)}}]}}
    wjson(os.path.join(RP, "definition", "pages", pg.name, "page.json"), pj)
    for v in pg.visuals:
        if pg is pages[0] and v["name"] == vid(pg.name, KPI_CAFE_KEY):
            v["filterConfig"] = year_filter(2025)
        wjson(os.path.join(RP, "definition", "pages", pg.name, "visuals", v["name"], "visual.json"), v)

wjson(os.path.join(RP, "definition.pbir"), {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
                                           "version": "4.0", "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}})
if not os.path.exists(os.path.join(RP, ".platform")):
    wjson(os.path.join(RP, ".platform"), {"$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
                                          "metadata": {"type": "Report", "displayName": NAME}, "config": {"version": "2.0", "logicalId": str(uuid.uuid4())}})
wjson(os.path.join(ROOT, f"{NAME}.pbip"), {"$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
                                          "version": "1.0", "artifacts": [{"report": {"path": f"{NAME}.Report"}}], "settings": {"enableAutoRecovery": True}})
with open(os.path.join(ROOT, ".gitignore"), "w") as f:
    f.write("**/.pbi/localSettings.json\n**/.pbi/cache.abf\n")
print("Rapport écrit :", RP, "| pages :", len(pages), "| visuels :", sum(len(pg.visuals) for pg in pages))
