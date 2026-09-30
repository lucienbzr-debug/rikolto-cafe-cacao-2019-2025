# -*- coding: utf-8 -*-
"""Pseudonymise les tables nettoyées avant publication.

Usage : python scripts/anonymiser.py <dossier des CSV nettoyés non anonymisés>

Ce qui est retiré ou remplacé :
- café  : numéro de carte membre -> code C-00001 (les doublons restent des doublons) ; village -> code V-001.
- cacao : code producteur -> M-001 (même numéro que l'ID ménage) ; latitude et longitude supprimées.
- Okapi : code planteur -> P-001 (les doublons restent des doublons) ; village -> code V-001.
Les indicateurs calculés (flags de doublon, âge, taille du ménage, revenus) ne changent pas,
donc tous les résultats du rapport, du deck et des dashboards restent identiques.
"""
import os, sys
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data")

def codes(series, prefix, width):
    """Remplace chaque valeur distincte par un code séquentiel (ordre de tri), les vides restent vides."""
    uniques = sorted(series.dropna().astype(str).unique())
    table = {v: f"{prefix}{i:0{width}d}" for i, v in enumerate(uniques, start=1)}
    return series.map(lambda v: table.get(str(v)) if pd.notna(v) else v)

def main(src):
    cafe = pd.read_csv(os.path.join(src, "fact_cafe_producteurs.csv"), encoding="utf-8-sig", low_memory=False)
    vill = pd.concat([cafe.Village, pd.read_csv(os.path.join(src, "fact_cacao_okapi_planteurs.csv"), encoding="utf-8-sig").Village])
    vmap = dict(zip(sorted(vill.dropna().astype(str).unique()), [f"V-{i:03d}" for i in range(1, 10000)]))
    cafe["Carte_Membre"] = codes(cafe.Carte_Membre, "C-", 5)
    cafe["Village"] = cafe.Village.map(lambda v: vmap.get(str(v)) if pd.notna(v) else v)
    cafe.to_csv(os.path.join(OUT, "fact_cafe_producteurs.csv"), index=False, encoding="utf-8-sig")

    men = pd.read_csv(os.path.join(src, "fact_cacao_menages.csv"), encoding="utf-8-sig")
    men["Code_Producteur"] = men.ID_Menage.map(lambda i: f"M-{int(i):03d}")
    men = men.drop(columns=[c for c in ("Latitude", "Longitude") if c in men.columns])
    men.to_csv(os.path.join(OUT, "fact_cacao_menages.csv"), index=False, encoding="utf-8-sig")

    oka = pd.read_csv(os.path.join(src, "fact_cacao_okapi_planteurs.csv"), encoding="utf-8-sig")
    oka["Code_Planteur"] = codes(oka.Code_Planteur, "P-", 3)
    oka["Village"] = oka.Village.map(lambda v: vmap.get(str(v)) if pd.notna(v) else v)
    oka.to_csv(os.path.join(OUT, "fact_cacao_okapi_planteurs.csv"), index=False, encoding="utf-8-sig")
    print("Tables pseudonymisées écrites dans", os.path.abspath(OUT))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
