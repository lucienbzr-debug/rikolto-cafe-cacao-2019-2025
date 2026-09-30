# Rikolto RDC · Café & Cacao 2019-2025

Analyse des bases café et cacao de Rikolto RDC pour la direction : diagnostic qualité, revenu vital des ménages cacao, tableau de bord et recommandations.

Le programme touche 3,2 fois plus de producteurs de café qu'en 2019 (12 184 en 2025), mais la base ne permet pas encore de démontrer un gain de revenu : production, chiffre d'affaires et marge y sont calculés par paramètres fixes. Côté cacao, 59 % des ménages dépassent le seuil de revenu vital de référence, et 40 % seulement une fois le seuil ajusté à la taille réelle des ménages (10,3 personnes).

> Analyse réalisée en septembre 2026 par Lucien Buzera. Les données publiées ici sont **pseudonymisées** (voir [Protection des données](#protection-des-données)).

## Livrables

| Livrable | Fichier | Contenu |
| --- | --- | --- |
| Rapport à la direction | [`livrables/Rapport_direction_Cafe_Cacao_2019-2025.docx`](livrables/Rapport_direction_Cafe_Cacao_2019-2025.docx) | 8 pages : synthèse, méthode, constats café et cacao, avis qualité pour le PV, 12 indicateurs bailleur, feuille de route |
| Deck comité de direction | [`livrables/Deck_Comite_direction_Cafe_Cacao.pptx`](livrables/Deck_Comite_direction_Cafe_Cacao.pptx) | 15 slides modifiables, graphiques natifs, notes d'orateur |
| Dashboard Power BI | [`powerbi/Rikolto_Cafe_Cacao.pbip`](powerbi/Rikolto_Cafe_Cacao.pbip) | 5 pages, 7 tables, 47 mesures DAX (format PBIP) |
| Dashboard Excel | [`livrables/Dashboard_Rikolto_Cafe_Cacao.xlsx`](livrables/Dashboard_Rikolto_Cafe_Cacao.xlsx) | Filtres campagne et coopérative, 233 formules, 6 graphiques |
| Dashboard HTML | [`livrables/Dashboard_Rikolto_Cafe_Cacao.html`](livrables/Dashboard_Rikolto_Cafe_Cacao.html) | Page autonome à ouvrir dans un navigateur, 5 onglets filtrables, thème clair et sombre |

Aperçu de la page Synthèse du dashboard Power BI :

![Page Synthèse du dashboard Power BI](powerbi/captures/1.%20Synth%C3%A8se%20direction.png)

## Résultats clés

| Indicateur | Valeur | Source |
| --- | --- | --- |
| Producteurs de café enregistrés, 2025 | 12 184 (3 864 en 2019) | Base café |
| Croissance des coopératives historiques CKK et COOKKANZ | +68 % | Base café |
| Part des femmes / des jeunes de 15-35 ans, 2025 | 25,6 % / 44,7 % | Base café |
| Rétention des producteurs 2024 → 2025 | 99,6 % | Base café |
| Revenu net médian d'un ménage cacao | 3 301 USD/an | Enquête revenu vital, mars 2024 |
| Ménages au-dessus du seuil de référence / du seuil ajusté | 59 % / 40 % | Enquête revenu vital |
| Ménages sous 2,15 USD par personne et par jour | 80 % | Enquête revenu vital |
| Part du cacao dans le revenu net | 87 % | Enquête revenu vital |
| Contrôles qualité : critiques / gravité élevée | 4 / 7 sur 23 | Registre qualité |

Seuil de revenu vital : Anker Research Institute, valeur de référence RDC rurale mise à jour 2025, 219 USD par mois soit 2 628 USD par an pour un ménage de 6 personnes. Le seuil ajusté est proportionnel à la taille réelle du ménage (438 USD par personne et par an).

## Organisation du dépôt

```
.
├── data/                     Tables nettoyées et pseudonymisées (CSV UTF-8) + dictionnaire
├── livrables/                Rapport Word, deck PowerPoint, dashboards Excel et HTML
├── powerbi/
│   ├── Rikolto_Cafe_Cacao.pbip          Projet Power BI (rapport PBIR + modèle TMDL)
│   ├── captures/                        Captures des 5 pages
│   └── _generateur/                     Scripts qui écrivent le modèle et les pages
└── scripts/
    ├── anonymiser.py                    Pseudonymisation appliquée avant publication
    └── exports/                         Génération des dashboards HTML et Excel, du Word et du PowerPoint
```

Le dictionnaire des colonnes se trouve dans [`data/README.md`](data/README.md).

## Ouvrir le dashboard Power BI

1. Installer Power BI Desktop (version récente, prise en charge du format PBIP).
2. Régénérer le modèle pour qu'il pointe vers le dossier `data/` de votre copie du dépôt :
   ```bash
   python powerbi/_generateur/build_model.py
   ```
3. Ouvrir `powerbi/Rikolto_Cafe_Cacao.pbip`, puis cliquer sur **Actualiser** pour charger les CSV.

Le paramètre Power Query `DossierDonnees` contient un chemin absolu. Vous pouvez aussi le modifier directement dans Power BI Desktop (Transformer les données › Gérer les paramètres).

## Régénérer les livrables

Prérequis : Python 3.10 ou plus récent avec `pandas`, `openpyxl`, `python-docx` ; Node.js 18 ou plus récent ; Microsoft Excel sous Windows pour recalculer les formules du classeur.

```bash
pip install pandas openpyxl python-docx
cd scripts/exports
python build_html.py        # livrables/Dashboard_Rikolto_Cafe_Cacao.html
python build_excel.py       # livrables/Dashboard_Rikolto_Cafe_Cacao.xlsx
python build_word.py        # livrables/Rapport_direction_Cafe_Cacao_2019-2025.docx
npm install
node build_pptx.js          # livrables/Deck_Comite_direction_Cafe_Cacao.pptx
```

Le classeur Excel est écrit par openpyxl sans valeurs calculées. Pour les calculer, ouvrez-le dans Excel ou lancez :

```powershell
powershell -ExecutionPolicy Bypass -File scripts/exports/recalc_excel.ps1 -Path "<chemin absolu>\livrables\Dashboard_Rikolto_Cafe_Cacao.xlsx"
```

Pour le dashboard Power BI : `python powerbi/_generateur/build_model.py` puis `python powerbi/_generateur/build_report.py`.

## Méthode en bref

- **Bases** : base consolidée Rikolto café 2019-2025 (42 433 lignes, 12 833 personnes, 4 coopératives) ; enquête Living Income Cacao Okapi de mars 2024 (88 ménages valides sur 90) ; liste des 301 planteurs Cacao Okapi.
- **Revenu cacao** : revenu net recalculé comme la somme de 7 sources. La variable `living_income` du questionnaire vaut revenu moins dépenses et n'est pas utilisée comme revenu.
- **Jeunes** : producteurs de 15 à 35 ans rapportés à l'ensemble des producteurs.
- **Rétention** : producteurs de la campagne N-1 présents en N ; non calculée si la coopérative comptait moins de 30 producteurs en N-1.
- **Qualité** : 23 contrôles de complétude, unicité, cohérence, validité et représentativité, consignés dans `data/qualite_controles.csv`.

La préparation des tables nettoyées à partir des fichiers Excel d'origine a été faite hors de ce dépôt. Les fichiers sources ne sont pas publiés.

## Limites

- Production, chiffre d'affaires et marge café sont **estimés** par paramètres fixes (densité, rendement par pied, prix unique de 0,55 USD/kg, marge forfaitaire de 60 %). Ils ne mesurent pas un revenu réel.
- L'enquête cacao compte 88 ménages dont 6 dirigés par des femmes : les résultats par sous-groupe sont indicatifs.
- 36 % des lignes café n'ont pas de territoire et 14 % pas de statut de certification.

## Protection des données

Les tables de `data/` ont été pseudonymisées avec [`scripts/anonymiser.py`](scripts/anonymiser.py) avant publication :

| Table | Traitement |
| --- | --- |
| `fact_cafe_producteurs.csv` | Numéro de carte membre remplacé par un code `C-00001` (les doublons restent des doublons) ; village remplacé par un code `V-001` |
| `fact_cacao_menages.csv` | Code producteur remplacé par `M-001` ; latitude et longitude supprimées |
| `fact_cacao_okapi_planteurs.csv` | Code planteur remplacé par `P-001` ; village remplacé par un code `V-001` |

Aucun résultat ne change : les indicateurs de doublon, l'âge, la taille des ménages et les revenus sont conservés. Territoire, collectivité, coopérative et section restent en clair. Les données appartiennent à Rikolto : ne rendez pas ce dépôt public sans son accord.

## Sources

- Rikolto RDC, *DONNEES_RIKOLTO_CONSOLIDEES 2019-2025* (base café).
- Rikolto RDC, enquête Living Income Cacao Okapi, mars 2024 (fichiers *Check sections* et *check yields*).
- Rikolto RDC, *Liste Cacao Okapi* (planteurs, 2024).
- Anker Research Institute, valeur de référence du revenu vital, RDC rurale, mise à jour 2025.
- Banque mondiale, seuil de pauvreté extrême de 2,15 USD par personne et par jour (PPA 2017).

## Droits

© 2026 Lucien Buzera et Rikolto RDC. Tous droits réservés. Aucune licence de réutilisation n'est accordée.
