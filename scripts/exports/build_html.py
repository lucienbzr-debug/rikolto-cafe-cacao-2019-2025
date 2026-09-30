# -*- coding: utf-8 -*-
"""Construit le dashboard HTML (version artifact + version autonome) à partir du gabarit et des données agrégées."""
import os, json
import aggregate
HERE = os.path.dirname(os.path.abspath(__file__))
data = json.dumps(aggregate.build(), ensure_ascii=False, separators=(",", ":")).replace("</", r"<\/")
tpl = open(os.path.join(HERE, "dashboard_template.html"), encoding="utf-8").read()
page = tpl.replace("__DATA__", data)
open(os.path.join(HERE, "dashboard_artifact.html"), "w", encoding="utf-8").write(page)
standalone = ('<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n'
              '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n</head>\n<body>\n'
              + page + '\n</body>\n</html>\n')
out = os.path.join(aggregate.LIVRABLES, "Dashboard_Rikolto_Cafe_Cacao.html")
open(out, "w", encoding="utf-8").write(standalone)
print(out, os.path.getsize(out), "octets")
