import re

with open("src/carteleria/lanzador_tv/la_cara_web/modules/columna4/tarjetas/tarjeta_chef.js", "r", encoding="utf-8") as f:
    text = f.read()

text = re.sub(r"<div class=\"asian-flash-condition\"><\/div>",
              "<div class=\"asian-flash-condition\">${escapeHtml(textoValidezOferta(item))}</div>", text)

with open("src/carteleria/lanzador_tv/la_cara_web/modules/columna4/tarjetas/tarjeta_chef.js", "w", encoding="utf-8", newline="") as f:
    f.write(text)
