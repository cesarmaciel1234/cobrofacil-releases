import re

with open("src/carteleria/lanzador_tv/la_cara_web/modules/columna4/tarjetas/tarjeta_chef.js", "r", encoding="utf-8") as f:
    text = f.read()

replacement = """<span class="asian-flash-social-text"><strong>${comprando}</strong> ${comprando === 1 ? 'FAMILIA ELIGE HOY' : 'FAMILIAS ELIGEN HOY'}</span>"""

text = re.sub(r'<span class="asian-flash-social-text"><strong>\$\{comprando\}</strong> comprando hoy</span>', replacement, text)

with open("src/carteleria/lanzador_tv/la_cara_web/modules/columna4/tarjetas/tarjeta_chef.js", "w", encoding="utf-8", newline="") as f:
    f.write(text)
