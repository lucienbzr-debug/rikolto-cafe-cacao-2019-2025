# -*- coding: utf-8 -*-
"""Agrège les tables propres pour les exports HTML et Excel du dashboard."""
import os, json
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))  # racine du dépôt
D = os.path.join(ROOT, "data")
LIVRABLES = os.path.join(ROOT, "livrables")

def load():
    cafe = pd.read_csv(os.path.join(D, "fact_cafe_producteurs.csv"), encoding="utf-8-sig")
    men = pd.read_csv(os.path.join(D, "fact_cacao_menages.csv"), encoding="utf-8-sig")
    src = pd.read_csv(os.path.join(D, "fact_cacao_sources_revenu.csv"), encoding="utf-8-sig")
    oka = pd.read_csv(os.path.join(D, "fact_cacao_okapi_planteurs.csv"), encoding="utf-8-sig")
    qc = pd.read_csv(os.path.join(D, "qualite_controles.csv"), encoding="utf-8-sig")
    par = pd.read_csv(os.path.join(D, "parametres.csv"), encoding="utf-8-sig")
    return cafe, men, src, oka, qc, par

def clean(df):
    """Enregistrements JSON valides : les valeurs manquantes deviennent null."""
    o = df.astype(object)
    return o.where(pd.notna(df), None).to_dict("records")

def cafe_cells(cafe):
    rows = []
    for (y, op), g in cafe.groupby(["Annee", "Cooperative"]):
        rows.append({
            "annee": int(y), "op": op, "n": len(g),
            "femmes": int((g.Sexe == "Femme").sum()),
            "jeunes": int((g.Classe_Age == "Jeune (15-35)").sum()),
            "age_connu": int(g.Classe_Age.notna().sum()),
            "sup": round(float(g.Superficie_ha.sum()), 2),
            "prod_t": round(float(g.Production_Cerise_kg.sum()) / 1000, 2),
            "ca": round(float(g.CA_USD.sum()), 0),
            "marge": round(float(g.Marge_USD.sum()), 0),
            "conforme": int((g.Certification == "Conforme").sum()),
            "conversion": int((g.Certification == "En conversion").sum()),
            "non_conforme": int((g.Certification == "Non conforme").sum()),
            "non_renseigne": int((g.Certification == "Non renseigné").sum()),
            "nouveaux": int(g.Nouveau.sum()),
            "present_n1": int(g.Present_N_1.sum()),
            "territoire_ok": int((g.Territoire != "Non renseigné").sum()),
            "doublon": int(g.Flag_Carte_Doublon.sum()),
            "uniques": int(g.ID_Producteur.nunique()),
        })
    return rows

def build():
    cafe, men, src, oka, qc, par = load()
    uniq = {
        "total": int(cafe.ID_Producteur.nunique()),
        "annee": {str(k): int(v) for k, v in cafe.groupby("Annee").ID_Producteur.nunique().items()},
        "op": {k: int(v) for k, v in cafe.groupby("Cooperative").ID_Producteur.nunique().items()},
        "fideles7": int(cafe.loc[cafe.Nb_Annees_Presence == 7, "ID_Producteur"].nunique()),
    }
    keep = ["ID_Menage", "Section", "Sexe", "Taille_Menage", "Superficie_Cacao_ha", "Rendement_kg_ha", "Prix_kg_USD",
            "Revenu_Net_Total_USD", "Seuil_LI_Ajuste_USD", "Atteint_LI_Menage_Ref", "Atteint_LI_Ajuste_Taille",
            "Revenu_par_personne_jour", "Depenses_Menage_USD", "Solde_Revenu_Depenses_USD", "Rev_Cacao", "Rev_Cafe", "Rev_Agroforesterie",
            "Rev_Autres_Cultures", "Rev_Elevage", "Rev_Hors_Ferme", "Rev_Transferts", "Flag_Outlier"]
    menages = clean(men[keep].round(3))
    okapi = []
    for s, g in oka.groupby("Section"):
        okapi.append({"section": s, "planteurs": len(g), "sup_tot": round(float(g.Superficie_Totale_ha.sum()), 2),
                      "sup_cacao": round(float(g.Superficie_Cacao_ha.sum()), 2)})
    qcr = clean(qc)
    params = {r.Parametre: float(r.Valeur) for r in par.itertuples()}
    return {"cafe": cafe_cells(cafe), "uniques": uniq, "menages": menages, "okapi": okapi,
            "qualite": qcr, "params": params, "sources_ordre": list(src.sort_values("Ordre").Source.unique())}

if __name__ == "__main__":
    data = build()
    out = os.path.join(os.path.dirname(__file__), "dashboard_data.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(out, os.path.getsize(out), "octets |", len(data["cafe"]), "cellules café")
