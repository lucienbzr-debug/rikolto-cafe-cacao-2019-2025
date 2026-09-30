# Tableau de bord Rikolto RDC · Café & Cacao 2019-2025 (Shiny, déployable sur Posit Connect Cloud)
# Données : agrégats café par campagne × coopérative et 88 ménages cacao sans identifiant (dossier donnees/).

library(shiny)
library(bslib)
library(dplyr)
library(plotly)
library(DT)

# ---------------------------------------------------------------- données
lire <- function(f) read.csv(file.path("donnees", f), encoding = "UTF-8", stringsAsFactors = FALSE, check.names = FALSE)
cafe      <- lire("cafe_campagne_op.csv")
uniques   <- lire("personnes_uniques.csv")
menages   <- lire("menages_cacao.csv")
okapi     <- lire("okapi_sections.csv")
qualite   <- lire("qualite_controles.csv")
params    <- lire("parametres.csv")
fideles7  <- lire("divers.csv")$valeur[1]

SEUIL     <- params$valeur[grepl("^Seuil revenu vital", params$parametre)]
PAUVRETE  <- params$valeur[grepl("pauvret", params$parametre)]
ANNEES    <- sort(unique(cafe$annee))
OPS       <- sort(unique(cafe$op))
SECTIONS  <- sort(unique(menages$Section))
GRAVITES  <- c("Critique", "Élevée", "Moyenne", "Faible")
MIN_N1    <- 30  # en dessous, la coopérative est considérée comme nouvelle : pas de taux de rétention

# ---------------------------------------------------------------- charte
COUL <- list(vert = "#1F5C4A", cafe = "#8C5A3C", sable = "#DDB690", ambre = "#B07A12", ardoise = "#4A6FA5",
             rouge = "#B23A48", sauge = "#9DBFAE", encre = "#1B2622", gris = "#56635C", fond = "#F1F3EF")
theme <- bs_theme(version = 5, bg = "#FCFCFA", fg = COUL$encre, primary = COUL$vert, secondary = COUL$cafe,
                  success = COUL$vert, warning = COUL$ambre, danger = COUL$rouge,
                  base_font = font_link("IBM Plex Sans", href = "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap"),
                  heading_font = font_link("Source Serif 4", href = "https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,600&display=swap"),
                  "navbar-bg" = COUL$vert)
theme <- bs_add_rules(theme, "
  body { background: #F1F3EF; }
  .bslib-value-box .value-box-title { font-size: .85rem; }
  .bslib-value-box .value-box-value { font-family: 'Source Serif 4', Georgia, serif; font-variant-numeric: tabular-nums; }
  .note { color: #56635C; font-size: .82rem; }
  .alerte { border-left: 4px solid #B23A48; background: #F6E4E6; padding: 12px 16px; border-radius: 0 8px 8px 0; }
  .alerte h5 { color: #B23A48; }
  .estime { font-size: .65rem; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: #B07A12; }")

# ---------------------------------------------------------------- formats
fr0 <- function(x) ifelse(is.na(x), "–", formatC(round(x), format = "d", big.mark = " "))
fr1 <- function(x) ifelse(is.na(x), "–", formatC(x, format = "f", digits = 1, decimal.mark = ","))
fr2 <- function(x) ifelse(is.na(x), "–", formatC(x, format = "f", digits = 2, decimal.mark = ","))
pct <- function(x, d = 1) ifelse(is.na(x), "–", paste0(formatC(100 * x, format = "f", digits = d, decimal.mark = ","), " %"))
vbox <- function(titre, valeur, note = NULL, theme_vb = "light") value_box(title = titre, value = valeur, if (!is.null(note)) p(class = "note", note), theme = theme_vb)
axe <- function(p, ...) layout(p, font = list(family = "IBM Plex Sans", color = COUL$encre), paper_bgcolor = "rgba(0,0,0,0)",
                              plot_bgcolor = "rgba(0,0,0,0)", legend = list(orientation = "h", y = 1.12), margin = list(t = 30), ...)
cfg <- function(p) config(p, displayModeBar = FALSE, locale = "fr")

# ---------------------------------------------------------------- calculs café
filtre_cafe <- function(an, o) {
  garder_an <- if (an == "Toutes") ANNEES else as.integer(an)
  garder_op <- if (o == "Toutes") OPS else o
  cafe[cafe$annee %in% garder_an & cafe$op %in% garder_op, , drop = FALSE]
}
somme <- function(df) df |> summarise(across(c(n, femmes, jeunes, sup, prod_t, ca, marge, conforme, conversion, non_conforme, non_renseigne, nouveaux, present_n1, territoire_ok, doublon), sum))
retention <- function(an, o) {
  df <- filtre_cafe(an, o); if (nrow(df) == 0) return(NA)
  y <- if (an == "Toutes") max(df$annee) else as.integer(an)
  cur <- somme(filtre_cafe(as.character(y), o)); prev <- somme(filtre_cafe(as.character(y - 1), o))
  if (is.na(prev$n) || prev$n < MIN_N1) NA else cur$present_n1 / prev$n
}
personnes <- function(an, o) uniques$personnes[uniques$annee == an & uniques$op == o][1]

# ---------------------------------------------------------------- calculs cacao
stats_cacao <- function(m) {
  sous <- m |> filter(Revenu_Net_Total_USD < Seuil_LI_Ajuste_USD)
  list(n = nrow(m), rev = median(m$Revenu_Net_Total_USD), ref = mean(m$Atteint_LI_Menage_Ref), adj = mean(m$Atteint_LI_Ajuste_Taille),
       ecart = if (nrow(sous)) median(sous$Seuil_LI_Ajuste_USD - sous$Revenu_Net_Total_USD) else NA,
       pcj = median(m$Revenu_par_personne_jour), sous215 = mean(m$Revenu_par_personne_jour < PAUVRETE),
       solde = mean(m$Solde_Revenu_Depenses_USD < 0), taille = mean(m$Taille_Menage),
       part_cacao = sum(m$Rev_Cacao) / sum(m$Revenu_Net_Total_USD), femmes = sum(m$Sexe == "Femme"))
}
SOURCES <- c(Rev_Cacao = "Cacao", Rev_Agroforesterie = "Agroforesterie", Rev_Hors_Ferme = "Activités hors ferme",
             Rev_Transferts = "Transferts et autres", Rev_Elevage = "Élevage", Rev_Cafe = "Café", Rev_Autres_Cultures = "Autres cultures vivrières")

# ---------------------------------------------------------------- interface
filtres_cafe <- function(id) layout_columns(col_widths = c(3, 3, 6),
  selectInput(paste0(id, "_annee"), "Campagne", c("Toutes", ANNEES)),
  selectInput(paste0(id, "_op"), "Coopérative", c("Toutes", OPS)),
  p(class = "note", style = "margin-top:2rem", "Les graphiques par campagne suivent le filtre Coopérative."))

ui <- page_navbar(
  title = "Rikolto RDC · Café & Cacao", theme = theme, fillable = FALSE, window_title = "Rikolto Café & Cacao",
  nav_panel("Synthèse",
    h3("Synthèse pour la direction"),
    p(class = "note", "Chiffres clés café (campagne 2025) et cacao (enquête revenu vital, mars 2024). Seuil Anker RDC rurale 2025 : ", fr0(SEUIL), " USD/an pour un ménage de 6 personnes."),
    uiOutput("synth_kpi"),
    layout_columns(col_widths = c(6, 6),
      card(card_header("Producteurs café enregistrés par campagne"), p(class = "note", "Doublement en 2024-2025 lié à l'intégration de COOPADE puis COOKURU"), plotlyOutput("synth_evol", height = 300)),
      card(card_header("Ménages cacao atteignant le revenu vital, par section"), p(class = "note", "Seuil de référence et seuil ajusté à la taille réelle du ménage"), plotlyOutput("synth_li", height = 300))),
    card(card_header("Messages clés"), uiOutput("synth_msg"))),
  nav_panel("Café · Bénéficiaires",
    h3("Café : bénéficiaires et inclusion"), filtres_cafe("b"), uiOutput("benef_kpi"),
    layout_columns(col_widths = c(7, 5),
      card(card_header("Producteurs par campagne et coopérative"), plotlyOutput("benef_coop", height = 300)),
      card(card_header("Part des femmes et des jeunes (15-35 ans)"), plotlyOutput("benef_incl", height = 300))),
    layout_columns(col_widths = c(8, 4),
      card(card_header("Profil des coopératives"), p(class = "note", "Selon la campagne sélectionnée · rétention vide pour une OP nouvelle"), DTOutput("benef_tab")),
      card(card_header("Statut de certification bio / fairtrade"), plotlyOutput("benef_cert", height = 280))),
    p(class = "note", "Rétention = producteurs de N-1 présents en N, calculée sur la dernière campagne sélectionnée. ", fr0(fideles7), " producteurs sont présents sur les 7 campagnes.")),
  nav_panel("Café · Économie",
    h3("Café : production et économie"), filtres_cafe("e"), uiOutput("eco_kpi"),
    layout_columns(col_widths = c(6, 6),
      card(card_header("Superficie déclarée et production estimée"), plotlyOutput("eco_prod", height = 300)),
      card(card_header("Marge estimée par producteur (USD)"), p(class = "note", "Marge = 60 % du CA pour 100 % des lignes : indicateur forfaitaire"), plotlyOutput("eco_marge", height = 280))),
    div(class = "alerte", h5("Pourquoi ces chiffres ne mesurent pas l'impact"),
      tags$ul(tags$li("Production = superficie × densité × rendement par pied ; les deux paramètres changent chaque année (1 000 → 1 620 pieds/ha ; 1,5 → 2,5 kg/pied)."),
              tags$li("Chiffre d'affaires = production × 0,55 USD/kg, un prix unique sur 7 ans."),
              tags$li("Coût = 40 % et marge = 60 % du CA pour 100 % des lignes.")),
      p(strong("Seule la superficie (0,55 ha en moyenne, stable) est déclarée. Recommandation : collecter les ventes réelles par producteur.")))),
  nav_panel("Cacao · Revenu vital",
    h3("Cacao : revenu des ménages et écart au revenu vital"),
    layout_columns(col_widths = c(3, 9), selectInput("c_section", "Section", c("Toutes", SECTIONS)),
      p(class = "note", style = "margin-top:2rem", "Enquête Living Income, 88 ménages Cacao Okapi, mars 2024. Échantillon indicatif (6 ménages dirigés par des femmes).")),
    uiOutput("cacao_kpi"),
    layout_columns(col_widths = c(6, 6),
      card(card_header("Revenu net médian par section (USD/an)"), p(class = "note", "Ligne pointillée : seuil de revenu vital"), plotlyOutput("cacao_rev", height = 300)),
      card(card_header("Composition du revenu net"), p(class = "note", "Forte dépendance au cacao : un choc de prix touche tout le revenu"), plotlyOutput("cacao_src", height = 300))),
    layout_columns(col_widths = c(6, 6),
      card(card_header("Leviers : rendement, prix, taille du ménage"), DTOutput("cacao_lev")),
      card(card_header("Base planteurs Cacao Okapi (301 planteurs)"), DTOutput("cacao_okapi")))),
  nav_panel("Qualité des données",
    h3("Qualité des données : diagnostic pour la validation"),
    layout_columns(col_widths = c(3, 3, 6), selectInput("q_base", "Base", c("Toutes", unique(qualite$Source))),
      selectInput("q_grav", "Gravité", c("Toutes", GRAVITES)),
      p(class = "note", style = "margin-top:2rem", "Avis proposé pour le PV : validation partielle. Base café valide comme référentiel des bénéficiaires, pas pour ses indicateurs économiques.")),
    uiOutput("q_kpi"),
    layout_columns(col_widths = c(8, 4),
      card(card_header("Registre des contrôles qualité"), DTOutput("q_tab")),
      card(card_header("Contrôles par dimension"), plotlyOutput("q_dim", height = 260)))),
  nav_spacer(),
  nav_item(tags$a("Code source", href = "https://github.com/lucienbzr-debug/rikolto-cafe-cacao-2019-2025", target = "_blank"))
)

# ---------------------------------------------------------------- serveur
server <- function(input, output, session) {
  # ----- Synthèse
  output$synth_kpi <- renderUI({
    s <- somme(filtre_cafe("2025", "Toutes")); m <- stats_cacao(menages)
    tagList(
      layout_columns(fill = FALSE, vbox("Producteurs café 2025", fr0(s$n)), vbox("Femmes", pct(s$femmes / s$n)), vbox("Jeunes 15-35 ans", pct(s$jeunes / s$n)),
                     vbox("Superficie café (ha)", fr0(s$sup)), vbox("Certifiés conformes", pct(s$conforme / s$n))),
      layout_columns(fill = FALSE, vbox("Ménages cacao enquêtés", m$n), vbox("Revenu net médian (USD/an)", fr0(m$rev), paste("Seuil :", fr0(SEUIL), "USD/an")),
                     vbox("Au-dessus du seuil (réf.)", pct(m$ref, 0)), vbox("Au-dessus du seuil ajusté", pct(m$adj, 0), paste("Taille réelle :", fr1(m$taille), "pers.")),
                     vbox("Contrôles critiques", paste(sum(qualite$Gravite == "Critique"), "/", nrow(qualite)), NULL, "danger")))
  })
  output$synth_evol <- renderPlotly({
    df <- cafe |> mutate(groupe = ifelse(op %in% c("CKK", "COOKKANZ"), "CKK et COOKKANZ (historiques)", "COOPADE et COOKURU (nouvelles)")) |>
      group_by(annee, groupe) |> summarise(n = sum(n), .groups = "drop")
    tot <- df |> group_by(annee) |> summarise(n = sum(n))
    plot_ly(df, x = ~factor(annee), y = ~n, color = ~groupe, colors = c(COUL$cafe, COUL$sable), type = "bar",
            hovertemplate = "%{x} : %{y:,} producteurs<extra>%{fullData.name}</extra>") |>
      add_annotations(data = tot, x = ~factor(annee), y = ~n, text = ~fr0(n), yanchor = "bottom", showarrow = FALSE, inherit = FALSE) |>
      axe(barmode = "stack", xaxis = list(title = ""), yaxis = list(title = "", separatethousands = TRUE)) |> cfg()
  })
  output$synth_li <- renderPlotly({
    df <- menages |> group_by(Section) |> summarise(ref = mean(Atteint_LI_Menage_Ref), adj = mean(Atteint_LI_Ajuste_Taille)) |> arrange(ref)
    df$Section <- factor(df$Section, levels = df$Section)
    plot_ly(df, y = ~Section, x = ~ref, type = "bar", orientation = "h", name = "Seuil de référence", marker = list(color = COUL$sauge),
            text = ~pct(ref, 0), textposition = "outside", hoverinfo = "none") |>
      add_trace(x = ~adj, name = "Seuil ajusté à la taille", marker = list(color = COUL$vert), text = ~pct(adj, 0)) |>
      axe(barmode = "group", xaxis = list(title = "", tickformat = ".0%", range = c(0, 1)), yaxis = list(title = "")) |> cfg()
  })
  output$synth_msg <- renderUI({
    s <- somme(filtre_cafe("2025", "Toutes")); m <- stats_cacao(menages)
    tags$ol(
      tags$li(strong("Couverture : "), fr0(s$n), " producteurs café en 2025 (×3,2 depuis 2019), ", pct(s$femmes / s$n), " de femmes et ", pct(s$jeunes / s$n), " de jeunes. Les coopératives historiques progressent de +68 %."),
      tags$li(strong("Revenu cacao : "), "revenu net médian de ", fr0(m$rev), " USD/an ; ", pct(m$ref, 0), " des ménages dépassent le seuil de référence, ", pct(m$adj, 0), " seulement une fois le seuil ajusté à la taille des ménages."),
      tags$li(strong("Vulnérabilité : "), pct(m$part_cacao, 0), " du revenu vient du cacao et ", pct(m$sous215, 0), " des ménages vivent avec moins de 2,15 USD par personne et par jour."),
      tags$li(style = paste0("color:", COUL$rouge, ";font-weight:600"), "Données : production, chiffre d'affaires et marge café sont calculés par paramètres fixes et ne mesurent pas l'impact."))
  })

  # ----- Café bénéficiaires
  output$benef_kpi <- renderUI({
    s <- somme(filtre_cafe(input$b_annee, input$b_op)); r <- retention(input$b_annee, input$b_op)
    layout_columns(fill = FALSE, vbox("Personnes", fr0(personnes(input$b_annee, input$b_op)), paste(fr0(s$n), "inscriptions")),
                   vbox("Nouveaux producteurs", fr0(s$nouveaux)), vbox("Rétention vs N-1", pct(r), if (is.na(r)) "Non applicable (2019 ou OP nouvelle)" else NULL),
                   vbox("Femmes", pct(s$femmes / s$n)), vbox("Jeunes 15-35 ans", pct(s$jeunes / s$n)))
  })
  output$benef_coop <- renderPlotly({
    df <- cafe |> filter(op %in% (if (input$b_op == "Toutes") OPS else input$b_op))
    plot_ly(df, x = ~factor(annee), y = ~n, color = ~op, colors = c(CKK = COUL$vert, COOKKANZ = COUL$cafe, COOKURU = COUL$ambre, COOPADE = COUL$ardoise),
            type = "bar", hovertemplate = "%{x} : %{y:,}<extra>%{fullData.name}</extra>") |>
      axe(barmode = "stack", xaxis = list(title = ""), yaxis = list(title = "")) |> cfg()
  })
  output$benef_incl <- renderPlotly({
    df <- cafe |> filter(op %in% (if (input$b_op == "Toutes") OPS else input$b_op)) |> group_by(annee) |>
      summarise(jeunes = sum(jeunes) / sum(n), femmes = sum(femmes) / sum(n))
    plot_ly(df, x = ~factor(annee), y = ~jeunes, type = "scatter", mode = "lines+markers", name = "Jeunes 15-35 ans",
            line = list(color = COUL$vert, width = 3), marker = list(color = COUL$vert), hovertemplate = "%{x} : %{y:.1%}<extra>Jeunes</extra>") |>
      add_trace(y = ~femmes, name = "Femmes", line = list(color = COUL$cafe, width = 3), marker = list(color = COUL$cafe), hovertemplate = "%{x} : %{y:.1%}<extra>Femmes</extra>") |>
      axe(xaxis = list(title = ""), yaxis = list(title = "", tickformat = ".0%", range = c(0, .7))) |> cfg()
  })
  output$benef_tab <- renderDT({
    lignes <- lapply(c(OPS, "Ensemble"), function(o) {
      oo <- if (o == "Ensemble") "Toutes" else o; s <- somme(filtre_cafe(input$b_annee, oo))
      if (is.na(s$n) || s$n == 0) return(NULL)
      data.frame(`Coopérative` = o, Producteurs = s$n, Femmes = s$femmes / s$n, Jeunes = s$jeunes / s$n, `Ha moyen` = s$sup / s$n,
                 Conformes = s$conforme / s$n, `Rétention` = retention(input$b_annee, oo), check.names = FALSE)
    })
    datatable(bind_rows(lignes), rownames = FALSE, options = list(dom = "t", ordering = FALSE), class = "compact") |>
      formatRound("Producteurs", 0, mark = " ") |> formatPercentage(c("Femmes", "Jeunes", "Conformes", "Rétention"), 1, dec.mark = ",") |>
      formatRound("Ha moyen", 2, dec.mark = ",") |>
      formatStyle("Femmes", color = styleInterval(0.15, c(COUL$rouge, COUL$encre))) |> formatStyle("Jeunes", color = styleInterval(0.3, c(COUL$rouge, COUL$encre)))
  })
  output$benef_cert <- renderPlotly({
    s <- somme(filtre_cafe(input$b_annee, input$b_op))
    plot_ly(labels = c("Conforme", "En conversion", "Non conforme", "Non renseigné"), values = c(s$conforme, s$conversion, s$non_conforme, s$non_renseigne),
            type = "pie", hole = .6, sort = FALSE, marker = list(colors = c(COUL$vert, COUL$ambre, COUL$rouge, "#DCE1DA")), textinfo = "percent") |>
      axe(showlegend = TRUE) |> cfg()
  })

  # ----- Café économie
  output$eco_kpi <- renderUI({
    s <- somme(filtre_cafe(input$e_annee, input$e_op)); est <- span(class = "estime", " estimé")
    layout_columns(fill = FALSE, vbox("Superficie déclarée (ha)", fr0(s$sup)), vbox("Superficie moyenne (ha)", fr2(s$sup / s$n)),
                   vbox(tagList("Production (t cerise)", est), fr0(s$prod_t)), vbox(tagList("Chiffre d'affaires (M USD)", est), fr1(s$ca / 1e6)),
                   vbox(tagList("Marge / producteur (USD)", est), fr0(s$marge / s$n)))
  })
  serie_op <- function(o) cafe[cafe$op %in% (if (o == "Toutes") OPS else o), ] |> group_by(annee) |>
    summarise(sup = sum(sup), prod_t = sum(prod_t), marge = sum(marge) / sum(n))
  output$eco_prod <- renderPlotly({
    df <- serie_op(input$e_op)
    plot_ly(df, x = ~factor(annee), y = ~sup, type = "bar", name = "Superficie déclarée (ha)", marker = list(color = COUL$sauge)) |>
      add_trace(y = ~prod_t, type = "scatter", mode = "lines+markers", name = "Production estimée (t cerise)", line = list(color = COUL$cafe, width = 3), marker = list(color = COUL$cafe)) |>
      axe(xaxis = list(title = ""), yaxis = list(title = "", separatethousands = TRUE)) |> cfg()
  })
  output$eco_marge <- renderPlotly({
    df <- serie_op(input$e_op)
    plot_ly(df, x = ~factor(annee), y = ~marge, type = "bar", marker = list(color = COUL$ambre), text = ~fr0(marge), textposition = "outside",
            hovertemplate = "%{x} : %{y:,.0f} USD<extra></extra>") |> axe(xaxis = list(title = ""), yaxis = list(title = "")) |> cfg()
  })

  # ----- Cacao
  mc <- reactive(if (input$c_section == "Toutes") menages else filter(menages, Section == input$c_section))
  output$cacao_kpi <- renderUI({
    m <- stats_cacao(mc())
    tagList(
      layout_columns(fill = FALSE, vbox("Revenu net médian (USD/an)", fr0(m$rev)), vbox("Seuil revenu vital (USD/an)", fr0(SEUIL), "Ménage de référence : 6 personnes"),
                     vbox("Au-dessus du seuil (réf.)", pct(m$ref, 0)), vbox("Au-dessus du seuil ajusté", pct(m$adj, 0)),
                     vbox("Écart médian au seuil ajusté", fr0(m$ecart), "USD/an, ménages sous le seuil"), vbox("Revenu / personne / jour", fr2(m$pcj), "USD, médiane")),
      layout_columns(fill = FALSE, vbox("Part du cacao dans le revenu", pct(m$part_cacao, 0), NULL, "danger"), vbox("Sous 2,15 USD / pers. / jour", pct(m$sous215, 0), NULL, "danger"),
                     vbox("Dépenses supérieures au revenu", pct(m$solde, 0), NULL, "danger"), vbox("Personnes par ménage", fr1(m$taille), "contre 6 (référence)", "danger")))
  })
  output$cacao_rev <- renderPlotly({
    df <- menages |> group_by(Section) |> summarise(rev = median(Revenu_Net_Total_USD)) |> arrange(desc(rev))
    df$Section <- factor(df$Section, levels = df$Section)
    df$coul <- ifelse(input$c_section %in% c("Toutes", as.character(df$Section)) & (input$c_section == "Toutes" | df$Section == input$c_section), COUL$vert, COUL$sauge)
    plot_ly(df, x = ~Section, y = ~rev, type = "bar", marker = list(color = ~coul), text = ~fr0(rev), textposition = "outside",
            hovertemplate = "%{x} : %{y:,.0f} USD/an<extra></extra>") |>
      axe(xaxis = list(title = ""), yaxis = list(title = "", range = c(0, 6000)),
          shapes = list(list(type = "line", xref = "paper", x0 = 0, x1 = 1, y0 = SEUIL, y1 = SEUIL, line = list(color = COUL$rouge, dash = "dash", width = 2)))) |> cfg()
  })
  output$cacao_src <- renderPlotly({
    m <- mc(); tot <- sum(m$Revenu_Net_Total_USD)
    df <- data.frame(source = unname(SOURCES), part = sapply(names(SOURCES), function(k) sum(m[[k]]) / tot))
    df$source <- factor(df$source, levels = rev(df$source))
    plot_ly(df, y = ~source, x = ~part, type = "bar", orientation = "h", marker = list(color = ifelse(df$source == "Cacao", COUL$cafe, COUL$sable)),
            text = ~pct(part), textposition = "outside", hoverinfo = "none") |>
      axe(xaxis = list(title = "", tickformat = ".0%", range = c(-0.05, 1.1)), yaxis = list(title = "")) |> cfg()
  })
  output$cacao_lev <- renderDT({
    df <- menages |> group_by(Section) |> summarise(`Ménages` = n(), Taille = mean(Taille_Menage), `Ha cacao` = median(Superficie_Cacao_ha),
                                                    `kg/ha` = median(Rendement_kg_ha), `USD/kg` = median(Prix_kg_USD))
    datatable(df, rownames = FALSE, options = list(dom = "t", ordering = FALSE), class = "compact") |>
      formatRound(c("Taille", "Ha cacao"), 1, dec.mark = ",") |> formatRound("kg/ha", 0) |> formatRound("USD/kg", 2, dec.mark = ",")
  })
  output$cacao_okapi <- renderDT({
    df <- okapi |> transmute(Section = section, Planteurs = planteurs, `Ha cacao` = sup_cacao, `Ha / planteur` = sup_cacao / planteurs, `% foncier en cacao` = sup_cacao / sup_tot)
    datatable(df, rownames = FALSE, options = list(dom = "t", ordering = FALSE), class = "compact") |>
      formatRound(c("Ha cacao"), 0) |> formatRound("Ha / planteur", 1, dec.mark = ",") |> formatPercentage("% foncier en cacao", 0)
  })

  # ----- Qualité
  qf <- reactive(qualite |> filter(input$q_base == "Toutes" | Source == input$q_base, input$q_grav == "Toutes" | Gravite == input$q_grav) |>
                   arrange(match(Gravite, GRAVITES), ID))
  output$q_kpi <- renderUI({
    q <- qf(); a <- somme(cafe)
    layout_columns(fill = FALSE, vbox("Contrôles affichés", nrow(q)), vbox("Critiques", sum(q$Gravite == "Critique"), NULL, "danger"),
                   vbox("Gravité élevée", sum(q$Gravite == "Élevée")), vbox("Territoire renseigné (café)", pct(a$territoire_ok / a$n)),
                   vbox("Cartes en doublon (café)", pct(a$doublon / a$n)))
  })
  output$q_tab <- renderDT({
    df <- qf() |> transmute(`Gravité` = Gravite, Base = Source, `Contrôle` = Controle, Anomalies = Nb_Anomalies, Taux = Taux, Impact = Commentaire)
    datatable(df, rownames = FALSE, options = list(pageLength = 12, dom = "tp", ordering = FALSE), class = "compact") |>
      formatRound("Anomalies", 0, mark = " ") |> formatPercentage("Taux", 1, dec.mark = ",") |>
      formatStyle("Gravité", fontWeight = "bold", color = styleEqual(GRAVITES, c(COUL$rouge, COUL$rouge, COUL$ambre, COUL$vert)))
  })
  output$q_dim <- renderPlotly({
    df <- qf() |> count(Dimension) |> arrange(n); df$Dimension <- factor(df$Dimension, levels = df$Dimension)
    plot_ly(df, y = ~Dimension, x = ~n, type = "bar", orientation = "h", marker = list(color = COUL$ardoise), text = ~n, textposition = "outside", hoverinfo = "none") |>
      axe(xaxis = list(title = "", dtick = 1), yaxis = list(title = "")) |> cfg()
  })
}

shinyApp(ui, server)
