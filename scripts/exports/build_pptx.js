// Génère la version PowerPoint modifiable du deck « Café & Cacao 2019-2025 – Comité de direction ».
// Mêmes contenus que le deck en ligne (deck_source/), graphiques natifs, notes d'orateur reprises des <aside>.
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const HERE = __dirname;
const OUT = path.join(HERE, "..", "..", "livrables", "Deck_Comite_direction_Cafe_Cacao.pptx");
const SRC = path.join(HERE, "deck_source");
const order = JSON.parse(fs.readFileSync(path.join(SRC, "deck.json"), "utf8")).order;
const notes = {};
for (const id of order) {
  const h = fs.readFileSync(path.join(SRC, "slides", id + ".html"), "utf8");
  const m = h.match(/<aside>([\s\S]*?)<\/aside>/);
  if (m) notes[id] = m[1].replace(/&amp;/g, "&").replace(/ /g, " ").trim();
}

// Palette et typographie (identiques au deck en ligne)
const C = { dark: "1E2A26", light: "F6F3EC", card: "FFFDF8", line: "E2DDD0", body: "4A514C", muted: "6B6F66",
  coffee: "9A5B2E", coffeeLt: "E3B98C", cacao: "2E6B55", cacaoLt: "A9CBB9", cacaoBg: "EEF2EE", alert: "A83A32", orange: "C77A32",
  brown: "5E3419", brownCard: "6E4125", brownTxt: "EBC79E", band: "F1ECE0", sand: "F4E8DC", mint: "E6EFEA", onDark: "C9D6CF" };
const HEAD = "Cambria", BODY = "Arial";
const W = 13.333, M = 0.89; // marges = 128 px du deck

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.title = "Café & Cacao 2019-2025 – Comité de direction";
pres.author = "Lucien Buzera";
pres.company = "Rikolto RDC";

let page = 0;
function slide(bg) { const s = pres.addSlide(); s.background = { color: bg }; page++; return s; }
function eyebrow(s, text, color) {
  s.addText(text.toUpperCase(), { x: M, y: 0.72, w: 11, h: 0.3, fontFace: BODY, fontSize: 12, bold: true, color, charSpacing: 2, margin: 0, isTextBox: true });
}
function title(s, text, opts = {}) {
  s.addText(text, { x: M, y: 1.05, w: opts.w || W - 2 * M, h: opts.h || 0.9, fontFace: HEAD, fontSize: opts.size || 32, bold: true,
    color: opts.color || C.dark, margin: 0, valign: "top", isTextBox: true });
}
function footer(s, text, color = C.muted) {
  if (text) s.addText(text, { x: M, y: 6.83, w: 10.4, h: 0.3, fontFace: BODY, fontSize: 11, color, margin: 0, isTextBox: true });
  s.addText(String(page), { x: W - M - 0.8, y: 6.83, w: 0.8, h: 0.3, fontFace: BODY, fontSize: 11, color, align: "right", margin: 0, isTextBox: true });
}
function card(s, x, y, w, h, fill = C.card, line = C.line) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: line, width: 0.75 }, rectRadius: 0.08 });
}
function note(s, id) { if (notes[id]) s.addNotes(notes[id]); }
const axisTxt = { catAxisLabelColor: C.body, valAxisLabelColor: C.muted, catAxisLabelFontFace: BODY, valAxisLabelFontFace: BODY,
  catAxisLabelFontSize: 11, valAxisLabelFontSize: 10, valGridLine: { color: "E6E1D6", size: 0.5 }, catGridLine: { style: "none" } };

// 1. Couverture
{ const s = slide(C.dark);
  s.addShape(pres.shapes.RECTANGLE, { x: M, y: 0.98, w: 0.33, h: 0.055, fill: { color: "C98A4B" }, line: { type: "none" } });
  s.addShape(pres.shapes.RECTANGLE, { x: M + 0.44, y: 0.98, w: 0.33, h: 0.055, fill: { color: "6FA88E" }, line: { type: "none" } });
  s.addText("RIKOLTO RDC · COMITÉ DE DIRECTION", { x: M + 0.9, y: 0.85, w: 9, h: 0.3, fontFace: BODY, fontSize: 14, bold: true, color: C.onDark, charSpacing: 3, margin: 0, isTextBox: true });
  s.addText("Café & Cacao\n2019-2025", { x: M, y: 2.3, w: 10, h: 2.0, fontFace: HEAD, fontSize: 60, bold: true, color: C.light, margin: 0, valign: "top", isTextBox: true });
  s.addText("Ce que la base démontre, ce qu'elle ne démontre pas encore, et les décisions à prendre", { x: M, y: 4.45, w: 9.2, h: 0.9, fontFace: BODY, fontSize: 22, color: C.onDark, margin: 0, valign: "top", isTextBox: true });
  s.addText("30 septembre 2026 · Préparé par Lucien Buzera", { x: M, y: 6.45, w: 9, h: 0.35, fontFace: BODY, fontSize: 14, color: C.onDark, margin: 0, isTextBox: true });
  note(s, "cover"); }

// 2. Synthèse
{ const s = slide(C.light); eyebrow(s, "Synthèse", C.coffee);
  title(s, "Le programme touche 3 fois plus de producteurs, mais la base ne prouve pas encore un gain de revenu", { h: 1.3, w: 10.8 });
  const cards = [["×3,2", "producteurs café : 12 184 en 2025 contre 3 864 en 2019", C.coffee], ["25,6 %", "de femmes en 2025, contre 21,6 % en 2019", C.coffee],
    ["40 %", "des ménages cacao atteignent le revenu vital ajusté à leur taille", C.cacao], ["100 %", "des chiffres économiques café sont calculés par formule, pas mesurés", C.alert]];
  const cw = (W - 2 * M - 3 * 0.22) / 4;
  cards.forEach(([n, t, col], i) => { const x = M + i * (cw + 0.22);
    card(s, x, 2.75, cw, 3.3); s.addShape(pres.shapes.RECTANGLE, { x: x + 0.02, y: 2.75, w: cw - 0.04, h: 0.06, fill: { color: col }, line: { type: "none" } });
    s.addText(n, { x: x + 0.28, y: 3.05, w: cw - 0.5, h: 0.9, fontFace: HEAD, fontSize: 40, bold: true, color: col, margin: 0, isTextBox: true });
    s.addText(t, { x: x + 0.28, y: 4.05, w: cw - 0.5, h: 1.8, fontFace: BODY, fontSize: 16, color: C.body, margin: 0, valign: "top", isTextBox: true }); });
  footer(s, "Sources : base consolidée Rikolto café 2019-2025 ; enquête Living Income Cacao Okapi, mars 2024 ; Anker 2025"); note(s, "synthese"); }

// 3. Décisions
{ const s = slide(C.light); eyebrow(s, "Décisions attendues", C.coffee); title(s, "Cinq décisions pour passer du comptage à la mesure");
  const items = [["Valider la base café", " comme référentiel des bénéficiaires, pas comme source d'indicateurs de revenu", C.coffee],
    ["Financer la collecte des ventes réelles", " par producteur de café dès la campagne 2026", C.coffee],
    ["Retenir le seuil ajusté", " à la taille du ménage comme indicateur principal de revenu vital cacao", C.cacao],
    ["Lancer la diversification des revenus cacao", ", en priorité à Babungwe et Mambasa", C.cacao],
    ["Adopter les 12 indicateurs bailleur", " proposés, dont 9 calculables dès aujourd'hui", C.dark]];
  items.forEach(([b, r, col], i) => { const y = 2.05 + i * 0.86;
    card(s, M, y, W - 2 * M, 0.72);
    s.addText(String(i + 1), { x: M + 0.25, y, w: 0.5, h: 0.72, fontFace: HEAD, fontSize: 24, bold: true, color: col, valign: "middle", margin: 0, isTextBox: true });
    s.addText([{ text: b, options: { bold: true, color: C.dark } }, { text: r, options: { color: C.dark } }],
      { x: M + 0.85, y, w: W - 2 * M - 1.1, h: 0.72, fontFace: BODY, fontSize: 16, valign: "middle", margin: 0, isTextBox: true }); });
  footer(s, null); note(s, "decisions"); }

// 4. Périmètre
{ const s = slide(C.light); eyebrow(s, "Périmètre et méthode", C.coffee); title(s, "Trois bases nettoyées et réunies dans un seul modèle");
  const hdr = ["Base", "Volume", "Période", "Usage"].map(t => ({ text: t, options: { bold: true, color: C.light, fill: { color: C.dark } } }));
  const rows = [["Base Rikolto café", "42 433 lignes, 12 833 personnes, 4 coopératives", "2019-2025", "Bénéficiaires, inclusion"],
    ["Enquête revenu vital cacao", "88 ménages valides sur 90", "Mars 2024", "Revenu, écart au seuil"],
    ["Planteurs Cacao Okapi", "301 planteurs, 5 sections", "2024", "Superficies, tiges"]]
    .map((r, i) => r.map(t => ({ text: t, options: { fill: { color: i % 2 ? C.band : C.card } } })));
  s.addTable([hdr, ...rows], { x: M, y: 2.05, w: W - 2 * M, colW: [3.0, 4.2, 1.8, 2.55], fontFace: BODY, fontSize: 14, color: C.dark,
    border: { type: "solid", color: C.line, pt: 0.75 }, rowH: 0.48, margin: [0.06, 0.1, 0.06, 0.1] });
    [[M, "Seuil de revenu vital", C.cacao, C.mint, "Anker, RDC rurale 2025 : 2 628 USD par an pour un ménage de 6 personnes. Seuil ajusté : 438 USD par personne, car les ménages comptent 10,3 personnes."],
     [M + (W - 2 * M) / 2 + 0.11, "Traitements clés", C.coffee, C.sand, "Revenu cacao recalculé sur 7 sources ; formules café reconstituées ; 23 contrôles qualité consignés dans un registre."]]
    .forEach(([x, h, col, bg, t]) => { const w = (W - 2 * M) / 2 - 0.11;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 4.35, w, h: 1.95, fill: { color: bg }, line: { type: "none" }, rectRadius: 0.08 });
      s.addText(h, { x: x + 0.28, y: 4.55, w: w - 0.5, h: 0.4, fontFace: BODY, fontSize: 16, bold: true, color: col, margin: 0, isTextBox: true });
      s.addText(t, { x: x + 0.28, y: 5.0, w: w - 0.5, h: 1.2, fontFace: BODY, fontSize: 14, color: C.dark, margin: 0, valign: "top", isTextBox: true }); });
  footer(s, null); note(s, "perimetre"); }

// 5. Couverture café
{ const s = slide(C.light); eyebrow(s, "Café · Couverture", C.coffee); title(s, "La hausse de 2024-2025 vient surtout de deux nouvelles coopératives", { w: 10.5, h: 1.2 });
  const yrs = ["2019", "2020", "2021", "2022", "2023", "2024", "2025"];
  s.addChart(pres.charts.BAR, [
    { name: "CKK et COOKKANZ (historiques)", labels: yrs, values: [3864, 4170, 4065, 4294, 4525, 5536, 6506] },
    { name: "COOPADE (2024) et COOKURU (2025)", labels: yrs, values: [0, 0, 0, 1, 4, 3790, 5678] }],
    { x: M, y: 2.35, w: 8.3, h: 4.35, barDir: "col", barGrouping: "stacked", chartColors: [C.coffee, C.coffeeLt], gapWidth: 45,
      showLegend: true, legendPos: "t", legendFontFace: BODY, legendFontSize: 11, legendColor: C.body, valAxisLabelFormatCode: "# ##0",
      showValue: false, ...axisTxt });
  [["+68 %", "pour les coopératives historiques : 3 864 → 6 506 producteurs", C.coffee, 2.6], ["99,6 %", "de rétention 2024 → 2025 ; 3 216 producteurs présents sur les 7 campagnes", C.cacao, 4.35]]
    .forEach(([n, t, col, y]) => { s.addText(n, { x: 9.55, y, w: 2.9, h: 0.75, fontFace: HEAD, fontSize: 36, bold: true, color: col, margin: 0, isTextBox: true });
      s.addText(t, { x: 9.55, y: y + 0.78, w: 2.9, h: 0.9, fontFace: BODY, fontSize: 14, color: C.body, margin: 0, valign: "top", isTextBox: true }); });
  footer(s, "Producteurs enregistrés par campagne · base consolidée Rikolto café 2019-2025"); note(s, "couverture"); }

// 6. Inclusion
{ const s = slide(C.light); eyebrow(s, "Café · Inclusion", C.coffee); title(s, "Plus de femmes, et des jeunes qui reviennent après la baisse de 2023", { w: 10.8, h: 1.2 });
  const yrs = ["2019", "2020", "2021", "2022", "2023", "2024", "2025"];
  s.addChart(pres.charts.LINE, [
    { name: "Jeunes 15-35 ans", labels: yrs, values: [0.608, 0.577, 0.515, 0.433, 0.324, 0.367, 0.447] },
    { name: "Femmes", labels: yrs, values: [0.216, 0.208, 0.208, 0.206, 0.209, 0.229, 0.256] }],
    { x: M, y: 2.35, w: 8.3, h: 4.35, chartColors: [C.cacao, C.orange], lineSize: 3, lineDataSymbol: "circle", lineDataSymbolSize: 7,
      showLegend: true, legendPos: "t", legendFontFace: BODY, legendFontSize: 11, legendColor: C.body,
      valAxisMinVal: 0, valAxisMaxVal: 0.7, valAxisLabelFormatCode: "0%", showValue: true, dataLabelFormatCode: "0.0%", dataLabelPosition: "t",
      dataLabelFontSize: 9, dataLabelColor: C.body, ...axisTxt });
  card(s, 9.55, 2.45, 2.9, 3.6);
  s.addText("Deux écarts ciblés", { x: 9.8, y: 2.65, w: 2.5, h: 0.4, fontFace: BODY, fontSize: 16, bold: true, color: C.dark, margin: 0, isTextBox: true });
  s.addText([{ text: "COOKKANZ : 12 % de femmes seulement.", options: { breakLine: true } }, { text: " ", options: { breakLine: true } },
    { text: "CKK : 24 % de jeunes seulement.", options: { breakLine: true } }, { text: " ", options: { breakLine: true } },
    { text: "La moyenne globale, tirée par les nouvelles OP, masque ces écarts." }],
    { x: 9.8, y: 3.15, w: 2.5, h: 2.7, fontFace: BODY, fontSize: 14, color: C.body, margin: 0, valign: "top", isTextBox: true });
  footer(s, "Part des producteurs café · jeunes = 15-35 ans, rapportés à l'ensemble des producteurs · base Rikolto café 2019-2025"); note(s, "inclusion"); }

// 7. Coopératives
{ const s = slide(C.light); eyebrow(s, "Café · Coopératives 2025", C.coffee); title(s, "87 % des producteurs sont certifiés ; COOKURU est encore en conversion", { w: 11, h: 1.2 });
  const H = ["Coopérative", "Producteurs", "Femmes", "Jeunes", "Ha moyen", "Certifiés"];
  const R = [["COOPADE", "4 082", "26,5 %", "49,8 %", "0,56", "100 %"], ["COOKKANZ", "3 316", "12,0 % (bas)", "56,2 %", "0,55", "100 %"],
    ["CKK", "3 190", "32,4 %", "23,6 % (bas)", "0,56", "100 %"], ["COOKURU", "1 596", "37,9 %", "50,1 %", "0,54", "0 % (conversion)"]];
  const rows = [H.map((t, j) => ({ text: t, options: { bold: true, color: C.light, fill: { color: C.dark }, align: j ? "right" : "left" } }))];
  R.forEach((r, i) => rows.push(r.map((t, j) => ({ text: t, options: { align: j ? "right" : "left", fill: { color: i % 2 ? C.band : C.card }, color: /bas/.test(t) ? C.alert : C.dark, bold: /bas/.test(t) } }))));
  rows.push(["Ensemble", "12 184", "25,6 %", "44,7 %", "0,56", "86,9 %"].map((t, j) => ({ text: t, options: { bold: true, align: j ? "right" : "left", fill: { color: C.mint } } })));
  s.addTable(rows, { x: M, y: 2.35, w: W - 2 * M, colW: [2.6, 1.9, 1.9, 1.9, 1.6, 1.65], fontFace: BODY, fontSize: 16, color: C.dark,
    border: { type: "solid", color: C.line, pt: 0.75 }, rowH: 0.52, margin: [0.06, 0.12, 0.06, 0.12] });
  s.addText("La superficie moyenne déclarée reste stable à 0,55 ha par producteur chaque année : c'est la donnée économique la plus fiable de la base.",
    { x: M, y: 5.75, w: 10.5, h: 0.7, fontFace: BODY, fontSize: 14, color: C.body, margin: 0, valign: "top", isTextBox: true });
  footer(s, "Campagne 2025 · jeunes = 15-35 ans · base consolidée Rikolto café"); note(s, "cooperatives"); }

// 8. Économie café (slide d'alerte)
{ const s = slide(C.brown); eyebrow(s, "Café · Production et économie", C.brownTxt);
  title(s, "Les chiffres économiques du café sont calculés, pas mesurés : ils ne prouvent pas un gain de revenu", { color: C.light, size: 34, h: 1.6, w: 11.3 });
  const cw = (W - 2 * M - 2 * 0.22) / 3;
  [["Production", "Superficie × densité × rendement par pied, deux paramètres qui changent chaque campagne"],
   ["Chiffre d'affaires", "Production × 0,55 USD/kg, un prix unique de 2019 à 2025"],
   ["Coût et marge", "Coût = 40 % du CA et marge = 60 % du CA, pour 100 % des lignes"]].forEach(([h, t], i) => { const x = M + i * (cw + 0.22);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 3.05, w: cw, h: 1.75, fill: { color: C.brownCard }, line: { type: "none" }, rectRadius: 0.08 });
    s.addText(h, { x: x + 0.28, y: 3.25, w: cw - 0.5, h: 0.4, fontFace: BODY, fontSize: 16, bold: true, color: C.brownTxt, margin: 0, isTextBox: true });
    s.addText(t, { x: x + 0.28, y: 3.7, w: cw - 0.5, h: 1.0, fontFace: BODY, fontSize: 14, color: C.light, margin: 0, valign: "top", isTextBox: true }); });
  s.addText([{ text: "Le CA estimé passe de 1,8 à 14,5 millions USD, mais la superficie moyenne ne bouge pas. " },
    { text: "Pour mesurer l'impact : enregistrer kilos livrés et prix payé par producteur.", options: { bold: true } }],
    { x: M, y: 5.2, w: 11.1, h: 0.9, fontFace: BODY, fontSize: 16, color: C.light, margin: 0, valign: "top", isTextBox: true });
  footer(s, "Formules reconstituées sur les 42 433 lignes de la base café", C.brownTxt); note(s, "economie"); }

// 9. Cacao revenu vital
{ const s = slide(C.cacaoBg); eyebrow(s, "Cacao · Revenu vital", C.cacao);
  title(s, "59 % au-dessus du seuil de référence, 40 % une fois la taille des ménages prise en compte", { w: 10.8, h: 1.2 });
  const secs = ["Mayuano", "Mungamba", "Mambasa", "Babungwe", "Ensemble"];
  s.addChart(pres.charts.BAR, [
    { name: "Seuil de référence (ménage de 6)", labels: secs, values: [0.76, 0.52, 0.59, 0.50, 0.59] },
    { name: "Seuil ajusté à la taille réelle", labels: secs, values: [0.71, 0.35, 0.27, 0.27, 0.40] }],
    { x: M, y: 2.3, w: 8.5, h: 4.4, barDir: "bar", barGrouping: "clustered", chartColors: [C.cacaoLt, C.cacao], gapWidth: 60, catAxisOrientation: "maxMin",
      valAxisMinVal: 0, valAxisMaxVal: 1, valAxisLabelFormatCode: "0%", showValue: true, dataLabelFormatCode: "0%", dataLabelPosition: "outEnd",
      dataLabelFontSize: 10, dataLabelColor: C.dark, showLegend: true, legendPos: "t", legendFontFace: BODY, legendFontSize: 11, legendColor: C.body, ...axisTxt });
  card(s, 9.75, 3.2, 2.7, 2.7, C.card, "D5DED8");
  s.addText("Pourquoi Mayuano ?", { x: 9.98, y: 3.4, w: 2.3, h: 0.4, fontFace: BODY, fontSize: 16, bold: true, color: C.cacao, margin: 0, isTextBox: true });
  s.addText("Rendement de 875 kg/ha, deux fois les autres sections, et ménages plus petits (7,8 personnes), malgré un prix moitié moindre.",
    { x: 9.98, y: 3.85, w: 2.3, h: 1.95, fontFace: BODY, fontSize: 13, color: C.body, margin: 0, valign: "top", isTextBox: true });
  footer(s, "Part des ménages au-dessus du seuil · enquête Living Income, mars 2024 (88 ménages) · Anker 2025 : 2 628 USD/an"); note(s, "cacao"); }

// 10. Vulnérabilité
{ const s = slide(C.cacaoBg); eyebrow(s, "Cacao · Vulnérabilité", C.cacao); title(s, "Des ménages grands, pauvres par personne et très dépendants du cacao", { w: 10.8, h: 1.2 });
  const T = [["80 %", "des ménages vivent avec moins de 2,15 USD par personne et par jour (médiane 0,97 USD)", C.alert],
    ["87 %", "du revenu net vient du cacao : une baisse du prix mondial toucherait presque tout le revenu", C.cacao],
    ["10,3", "personnes par ménage en moyenne, contre 6 dans le ménage de référence Anker", C.dark],
    ["2 225", "USD par an manquent au ménage médian sous le seuil ajusté", C.dark]];
  const cw = (W - 2 * M - 0.22) / 2;
  T.forEach(([n, t, col], i) => { const x = M + (i % 2) * (cw + 0.22), y = 2.4 + Math.floor(i / 2) * 1.62;
    card(s, x, y, cw, 1.42, C.card, "D5DED8");
    s.addText(n, { x: x + 0.28, y, w: 1.9, h: 1.42, fontFace: HEAD, fontSize: 40, bold: true, color: col, valign: "middle", margin: 0, isTextBox: true });
    s.addText(t, { x: x + 2.25, y, w: cw - 2.5, h: 1.42, fontFace: BODY, fontSize: 14, color: C.body, valign: "middle", margin: 0, isTextBox: true }); });
  s.addText([{ text: "Leviers : ", options: { bold: true } }, { text: "rendement (38 % des superficies non productives), diversification (13 % du revenu hors cacao) et qualité, qui fait le prix." }],
    { x: M, y: 5.75, w: 11.4, h: 0.6, fontFace: BODY, fontSize: 14, color: C.body, margin: 0, valign: "top", isTextBox: true });
  footer(s, "Enquête Living Income Cacao Okapi, mars 2024 · 88 ménages dont 6 femmes : résultats indicatifs"); note(s, "vulnerabilite"); }

// 11. Qualité
{ const s = slide(C.light); eyebrow(s, "Qualité des données", C.alert); title(s, "Avis proposé pour le PV : validation partielle");
  [["23", "contrôles réalisés", C.dark], ["4", "critiques", C.alert], ["7", "de gravité élevée", C.orange]].forEach(([n, t, col], i) => {
    s.addText(n, { x: M, y: 2.1 + i * 0.95, w: 0.95, h: 0.85, fontFace: HEAD, fontSize: 44, bold: true, color: col, margin: 0, valign: "middle", isTextBox: true });
    s.addText(t, { x: M + 1.0, y: 2.1 + i * 0.95, w: 2.0, h: 0.85, fontFace: BODY, fontSize: 14, color: C.body, margin: 0, valign: "middle", isTextBox: true }); });
  s.addText("Valider la base café pour les bénéficiaires, pas pour ses indicateurs économiques.",
    { x: M, y: 5.05, w: 2.9, h: 1.1, fontFace: BODY, fontSize: 14, color: C.body, margin: 0, valign: "top", isTextBox: true });
  const R = [["Critique", "Production, CA, marge café calculés", "Collecter les ventes réelles"], ["Critique", "« living_income » = revenu − dépenses", "Renommer, utiliser le revenu net"],
    ["Élevée", "Territoire manquant (36 %)", "Compléter via village → territoire"], ["Élevée", "Certification non renseignée (14 %)", "Reprendre les rapports d'audit"],
    ["Élevée", "2 099 lignes à carte partagée", "Dédoublonner avec les OP"], ["Élevée", "Rupture de série 2024", "Séparer historique et nouvelles OP"]];
  const rows = [["Gravité", "Anomalie", "Action"].map(t => ({ text: t, options: { bold: true, color: C.light, fill: { color: C.dark } } }))];
  R.forEach((r, i) => rows.push(r.map((t, j) => ({ text: t, options: { fill: { color: i % 2 ? C.band : C.card }, color: j ? C.dark : (t === "Critique" ? C.alert : C.coffee), bold: j === 0 } }))));
  s.addTable(rows, { x: 4.1, y: 2.1, w: W - M - 4.1, colW: [1.45, 3.8, 3.1], fontFace: BODY, fontSize: 13, color: C.dark,
    border: { type: "solid", color: C.line, pt: 0.75 }, rowH: 0.5, margin: [0.06, 0.1, 0.06, 0.1] });
  footer(s, "Registre complet : page Qualité du dashboard et fichier qualite_controles.csv, à annexer au PV"); note(s, "qualite"); }

// 12. Indicateurs bailleur
{ const s = slide(C.light); eyebrow(s, "Reporting bailleur", C.coffee); title(s, "12 indicateurs bailleur : 9 disponibles, 3 à collecter", { w: 11.5 });
  const R = [["Producteurs de café appuyés", "12 184 (2025)", "Bonne"], ["Part des femmes parmi les producteurs de café", "25,6 %", "Bonne"],
    ["Part des jeunes de 15-35 ans", "44,7 %", "Bonne"], ["Taux de rétention annuel des membres", "99,6 %", "Bonne"],
    ["Producteurs certifiés bio / fairtrade conformes", "86,9 %", "Moyenne"], ["Superficie de café sous gestion certifiée", "6 770 ha", "Moyenne"],
    ["Ménages cacao au revenu vital (seuil ajusté)", "40 % (2024)", "Indicative"], ["Écart médian au revenu vital sous le seuil", "2 225 USD/an", "Indicative"],
    ["Part du cacao dans le revenu net", "87 %", "Indicative"], ["Revenu net café par producteur", "À mesurer", "Collecte à créer"],
    ["Prix moyen payé au producteur de café", "À mesurer", "Collecte à créer"], ["Rendement cacao par ha productif", "567 kg/ha", "Suivi annuel à créer"]];
  const rows = [["N°", "Indicateur", "Valeur actuelle", "Fiabilité"].map(t => ({ text: t, options: { bold: true, color: C.light, fill: { color: C.dark } } }))];
  R.forEach((r, i) => rows.push([String(i + 1), ...r].map(t => ({ text: t, options: { fill: { color: i >= 9 ? C.sand : (i % 2 ? C.band : C.card) } } }))));
  s.addTable(rows, { x: M, y: 1.85, w: W - 2 * M, colW: [0.6, 6.35, 2.3, 2.3], fontFace: BODY, fontSize: 12, color: C.dark,
    border: { type: "solid", color: C.line, pt: 0.75 }, rowH: 0.34, margin: [0.03, 0.1, 0.03, 0.1] });
  footer(s, "Indicateurs 7 à 9 : refaire l'enquête tous les 2 ans, sur au moins 200 ménages dont 30 % de femmes"); note(s, "indicateurs"); }

// 13. Feuille de route
{ const s = slide(C.light); eyebrow(s, "Feuille de route", C.coffee); title(s, "Fiabiliser la base d'ici fin 2026, mesurer les revenus réels en 2027", { w: 11, h: 1.2 });
  const P = [["1. Fiabiliser la base", "Octobre – décembre 2026", ["Dédoublonner 2 099 lignes", "Compléter territoire et certification", "Renommer living_income", "Signer le PV de validation partielle"], true],
    ["2. Préparer la mesure", "Janvier – mars 2027", ["Module ventes réelles : kilos livrés et prix payé", "Échantillon revenu vital : 200 ménages, 30 % de femmes", "Former les 4 coopératives"], false],
    ["3. Mesurer et agir", "Campagne 2027", ["Collecter les ventes réelles", "2e vague revenu vital cacao", "Diversification à Babungwe et Mambasa", "Cibler femmes (COOKKANZ) et jeunes (CKK)"], false]];
  const gate = 0.85, cw = (W - 2 * M - 2 * gate) / 3;
  P.forEach(([h, d, items, main], i) => { const x = M + i * (cw + gate);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 2.35, w: cw, h: 3.9, fill: { color: C.card }, line: { color: main ? C.coffee : C.line, width: main ? 2 : 0.75 }, rectRadius: 0.08 });
    s.addText(h, { x: x + 0.25, y: 2.55, w: cw - 0.45, h: 0.45, fontFace: BODY, fontSize: 18, bold: true, color: main ? C.coffee : C.dark, margin: 0, isTextBox: true });
    s.addText(d, { x: x + 0.25, y: 3.02, w: cw - 0.45, h: 0.35, fontFace: BODY, fontSize: 13, color: C.muted, margin: 0, isTextBox: true });
    s.addText(items.map((t, k) => ({ text: t, options: { bullet: true, breakLine: k < items.length - 1 } })),
      { x: x + 0.2, y: 3.5, w: cw - 0.4, h: 2.6, fontFace: BODY, fontSize: 13, color: C.dark, paraSpaceAfter: 6, valign: "top", margin: 0, isTextBox: true });
    if (i < 2) { const gx = x + cw + gate / 2;
      s.addShape(pres.shapes.DIAMOND, { x: gx - 0.17, y: 3.95, w: 0.34, h: 0.34, fill: { color: C.coffeeLt }, line: { color: C.coffee, width: 1.25 } });
      s.addText(i ? "Outils testés" : "PV signé", { x: gx - 0.36, y: 4.35, w: 0.72, h: 0.6, fontFace: BODY, fontSize: 10, color: C.body, align: "center", margin: 0, isTextBox: true }); } });
  footer(s, null); note(s, "feuille"); }

// 14. Dashboard
{ const s = slide(C.light); eyebrow(s, "Pilotage", C.coffee); title(s, "Tous ces chiffres, sur un seul écran Power BI");
  const iw = 8.3, ih = iw * 742 / 1442;
  s.addImage({ path: path.join(SRC, "dashboard_synthese.png"), x: M, y: 1.95, w: iw, h: ih,
    altText: "Page Synthèse direction du dashboard Power BI : cartes café 2025 et cacao, producteurs par campagne, ménages au revenu vital par section, messages clés et contrôles qualité" });
  s.addText("5 pages", { x: 9.6, y: 2.0, w: 2.9, h: 0.45, fontFace: BODY, fontSize: 18, bold: true, color: C.dark, margin: 0, isTextBox: true });
  const pages = ["Synthèse", "Café : bénéficiaires", "Café : économie", "Cacao : revenu vital", "Qualité des données"];
  s.addText(pages.map((t, k) => ({ text: t, options: { bullet: { type: "number" }, breakLine: k < pages.length - 1 } })),
    { x: 9.6, y: 2.55, w: 2.9, h: 2.0, fontFace: BODY, fontSize: 14, color: C.body, paraSpaceAfter: 4, valign: "top", margin: 0, isTextBox: true });
  s.addText("À revoir chaque trimestre, avec la page Qualité à l'ordre du jour.", { x: 9.6, y: 4.75, w: 2.9, h: 0.9, fontFace: BODY, fontSize: 14, color: C.body, margin: 0, valign: "top", isTextBox: true });
  footer(s, "Page « Synthèse direction » · Rikolto_Cafe_Cacao.pbip · cartes café : campagne 2025"); note(s, "dashboard"); }

// 15. Clôture
{ const s = slide(C.dark); eyebrow(s, "Pour aller plus loin", "C98A4B"); title(s, "Trois livrables pour suivre ces décisions", { color: C.light, size: 36 });
  const cw = (W - 2 * M - 2 * 0.22) / 3;
  [["Rapport écrit", "Constats détaillés, méthode, avis qualité et indicateurs bailleur"], ["Dashboard Power BI", "5 pages, à revoir en comité de direction chaque trimestre"],
   ["Données nettoyées", "6 fichiers CSV et le registre des 23 contrôles qualité"]].forEach(([h, t], i) => { const x = M + i * (cw + 0.22);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 3.2, w: cw, h: 1.7, fill: { color: "2A3833" }, line: { type: "none" }, rectRadius: 0.08 });
    s.addText(h, { x: x + 0.28, y: 3.42, w: cw - 0.5, h: 0.45, fontFace: BODY, fontSize: 18, bold: true, color: C.light, margin: 0, isTextBox: true });
    s.addText(t, { x: x + 0.28, y: 3.92, w: cw - 0.5, h: 0.9, fontFace: BODY, fontSize: 14, color: C.onDark, margin: 0, valign: "top", isTextBox: true }); });
  s.addText("Questions et discussion", { x: M, y: 6.3, w: 6, h: 0.45, fontFace: BODY, fontSize: 16, color: C.onDark, margin: 0, isTextBox: true });
  note(s, "fin"); }

pres.writeFile({ fileName: OUT }).then(f => console.log(f));
