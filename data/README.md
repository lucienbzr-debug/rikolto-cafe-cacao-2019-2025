# Dictionnaire des données

Six tables CSV (UTF-8 avec BOM, séparateur virgule, point décimal). Les identifiants personnels sont pseudonymisés (voir le [README principal](../README.md#protection-des-données)).

| Fichier | Lignes | Grain |
| --- | --- | --- |
| `fact_cafe_producteurs.csv` | 42 433 | Un producteur de café par campagne, 2019-2025 |
| `fact_cacao_menages.csv` | 88 | Un ménage de l'enquête revenu vital, mars 2024 |
| `fact_cacao_sources_revenu.csv` | 616 | Un ménage × une source de revenu (88 × 7) |
| `fact_cacao_okapi_planteurs.csv` | 301 | Un planteur de la liste Cacao Okapi, 2024 |
| `qualite_controles.csv` | 23 | Un contrôle qualité du registre |
| `parametres.csv` | 3 | Un seuil utilisé dans l'analyse, avec sa source |

## fact_cafe_producteurs.csv

| Colonne | Description |
| --- | --- |
| `ID_Saison` | Identifiant de la ligne (producteur × campagne) |
| `ID_Producteur` | Identifiant longitudinal du producteur (nom + sexe + OP dans la base d'origine), numérique |
| `Sexe`, `Age`, `Classe_Age` | Sexe ; âge déclaré ; `Jeune (15-35)` ou `Adulte (36+)` (vide si âge inconnu) |
| `Cooperative` | CKK, COOKKANZ, COOPADE (depuis 2024) ou COOKURU (depuis 2025) |
| `Village` | Code pseudonyme `V-001` |
| `Collectivite`, `Territoire` | Unités administratives ; `Non renseigné` si absent |
| `Annee` | Campagne (2019 à 2025) |
| `Carte_Membre` | Code pseudonyme `C-00001` ; deux lignes d'une même campagne avec le même code partagent une carte |
| `Superficie_ha`, `Nb_Pieds` | Superficie caféière et nombre de pieds déclarés |
| `Production_Cerise_kg`, `Production_Parche_kg` | Production **estimée** = superficie × densité × rendement par pied |
| `CA_USD`, `Cout_USD`, `Marge_USD` | **Estimés** : CA = production × 0,55 USD/kg ; coût = 40 % et marge = 60 % du CA |
| `Certification` | `Conforme`, `En conversion`, `Non conforme` ou `Non renseigné` |
| `Superficie_GIFS_ha`, `Annee_Adhesion`, `Cotisation_USD` | Champs complémentaires de la base d'origine |
| `Nb_Annees_Presence` | Nombre de campagnes où le producteur apparaît (1 à 7) |
| `Nouveau`, `Present_N_1` | 1 si première apparition ; 1 si présent la campagne précédente |
| `Flag_Carte_Doublon`, `Flag_Age_Incoherent` | Contrôles qualité : carte partagée sur une campagne ; écart d'âge incohérent d'une année à l'autre |
| `Param_Densite`, `Param_Rdt_Pied`, `Param_Taux_Parche` | Paramètres fixes utilisés par la base pour calculer la production |

## fact_cacao_menages.csv

| Colonne | Description |
| --- | --- |
| `ID_Menage`, `Code_Producteur` | Identifiant du ménage ; code pseudonyme `M-001` |
| `Section` | Babungwe, Mambasa, Mayuano ou Mungamba |
| `Age`, `Sexe`, `Taille_Menage` | Âge et sexe du chef de ménage ; nombre de personnes |
| `Superficie_Cacao_ha`, `Superficie_Productive_ha` | Superficie cacao totale et en production |
| `Production_Cacao_kg`, `Vente_Cacao_kg`, `Rendement_kg_ha`, `Prix_kg_USD` | Production, ventes, rendement et prix de vente moyen |
| `Recette_Cacao_USD`, `Cout_Cacao_USD` | Recette brute et coûts de production du cacao |
| `Rev_Cacao` … `Rev_Transferts` | Revenu net par source (7 sources, négatif possible) |
| `Revenu_Net_Total_USD` | Somme des 7 sources |
| `Depenses_Menage_USD`, `Solde_Revenu_Depenses_USD` | Dépenses déclarées ; revenu moins dépenses (variable `living_income` du questionnaire) |
| `Seuil_LI_Ajuste_USD` | Seuil de revenu vital proportionnel à la taille du ménage (438 USD par personne et par an) |
| `Atteint_LI_Menage_Ref`, `Atteint_LI_Ajuste_Taille` | 1 si le revenu net atteint le seuil de 2 628 USD ; 1 s'il atteint le seuil ajusté |
| `Revenu_par_personne_jour` | Revenu net / taille du ménage / 365 |
| `Certifie`, `Forme`, `Credit` | 1 si certifié, formé, ayant accès au crédit |
| `Flag_Outlier` | 1 pour les valeurs extrêmes à vérifier sur le terrain |

## fact_cacao_sources_revenu.csv

`ID_Menage`, `Source` (libellé de la source), `Ordre` (0 = cacao, pour le tri), `Montant_USD` (revenu net de la source).

## fact_cacao_okapi_planteurs.csv

| Colonne | Description |
| --- | --- |
| `Code_Planteur` | Code pseudonyme `P-001` ; les doublons de la liste d'origine sont conservés |
| `Section`, `Axe`, `Corporation` | Rattachement géographique et organisationnel |
| `Village` | Code pseudonyme `V-001` |
| `Superficie_Totale_ha`, `Superficie_Cacao_ha`, `Nb_Tiges`, `Annee_Plantation` | Foncier, superficie cacao, tiges (souvent estimées à 1 100 par ha), année de plantation |
| `Flag_Code_Doublon`, `Flag_Sup_Incoherente` | Code en doublon ; superficie cacao supérieure à la superficie totale |

## qualite_controles.csv

`ID`, `Source` (base contrôlée), `Dimension` (complétude, unicité, cohérence, validité, représentativité), `Controle`, `Nb_Anomalies`, `Nb_Total`, `Taux`, `Gravite` (Critique, Élevée, Moyenne, Faible), `Commentaire`.

## parametres.csv

`Parametre`, `Valeur`, `Source` : seuil de revenu vital Anker (2 628 USD/an), taille du ménage de référence (6), seuil de pauvreté extrême Banque mondiale (2,15 USD par personne et par jour).
