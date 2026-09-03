import re

with open("src/carteleria/lanzador_tv/la_cara_web/modules/columna4/tarjetas/tarjeta_chef.js", "r", encoding="utf-8") as f:
    text = f.read()

replacement = """
        if (vendidosReales > 0) {
            comprando = vendidosReales;
            mostrarVendido = Math.min(99, Math.round(vendidosReales));
"""

text = re.sub(r'\n\s*if \(vendidosReales > 0\) \{\s*comprando = vendidosReales;\s*mostrarVendido = Math\.round\(vendidosReales\);', replacement, text)

with open("src/carteleria/lanzador_tv/la_cara_web/modules/columna4/tarjetas/tarjeta_chef.js", "w", encoding="utf-8", newline="") as f:
    f.write(text)
