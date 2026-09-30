# -*- coding: utf-8 -*-
"""Écrit les tables de l'application Shiny (posit/donnees) : café agrégé par campagne × coopérative,
personnes uniques, ménages cacao (sans identifiant), sources de revenu, Okapi par section, qualité, paramètres."""
import os
import pandas as pd
import aggregate

OUT = os.path.join(aggregate.ROOT, "posit", "donnees")
os.makedirs(OUT, exist_ok=True)
d = aggregate.build()
pd.DataFrame(d["cafe"]).to_csv(os.path.join(OUT, "cafe_campagne_op.csv"), index=False, encoding="utf-8")
u = d["uniques"]
rows = [{"annee": "Toutes", "op": "Toutes", "personnes": u["total"]}]
rows += [{"annee": a, "op": "Toutes", "personnes": v} for a, v in u["annee"].items()]
rows += [{"annee": "Toutes", "op": o, "personnes": v} for o, v in u["op"].items()]
rows += [{"annee": str(c["annee"]), "op": c["op"], "personnes": c["uniques"]} for c in d["cafe"]]
pd.DataFrame(rows).to_csv(os.path.join(OUT, "personnes_uniques.csv"), index=False, encoding="utf-8")
pd.DataFrame(d["menages"]).drop(columns=["ID_Menage"]).to_csv(os.path.join(OUT, "menages_cacao.csv"), index=False, encoding="utf-8")
pd.DataFrame(d["okapi"]).to_csv(os.path.join(OUT, "okapi_sections.csv"), index=False, encoding="utf-8")
pd.DataFrame(d["qualite"]).to_csv(os.path.join(OUT, "qualite_controles.csv"), index=False, encoding="utf-8")
pd.DataFrame([{"parametre": k, "valeur": v} for k, v in d["params"].items()]).to_csv(os.path.join(OUT, "parametres.csv"), index=False, encoding="utf-8")
pd.Series({"fideles_7_campagnes": u["fideles7"]}).to_frame("valeur").to_csv(os.path.join(OUT, "divers.csv"), encoding="utf-8")
print("Données Posit écrites dans", OUT, sorted(os.listdir(OUT)))
