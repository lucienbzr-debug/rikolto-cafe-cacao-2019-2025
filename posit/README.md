# Application Shiny · Posit Connect Cloud

Version Shiny (R) du tableau de bord : 5 onglets, filtres campagne, coopérative, section, base et gravité.

- `app.R` : l'application (shiny, bslib, plotly, DT, dplyr).
- `donnees/` : agrégats café par campagne × coopérative et 88 ménages cacao **sans identifiant**, écrits par `scripts/exports/build_posit_data.py`.
- `manifest.json` : dépendances R pour Posit Connect Cloud, écrit par `rsconnect::writeManifest()`.

## Publier sur Posit Connect Cloud

1. Se connecter sur [connect.posit.cloud](https://connect.posit.cloud) avec le compte lié à GitHub.
2. **Publish** › **Shiny** › dépôt `lucienbzr-debug/rikolto-cafe-cacao-2019-2025`, branche `main`.
3. Fichier principal : `posit/app.R`, puis **Publish**.

À chaque `git push` sur `main`, Connect Cloud peut redéployer l'application automatiquement.

## Lancer en local

```r
shiny::runApp("posit")
```

Après une modification de `app.R` ou des données, régénérer le manifest depuis le dossier `posit/` :

```r
rsconnect::writeManifest(appDir = ".", appPrimaryDoc = "app.R",
                         appFiles = c("app.R", list.files("donnees", full.names = TRUE)))
```
