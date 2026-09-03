import re

with open("src/carteleria/lanzador_tv/la_cara_web/modules/columna4/tarjetas/tarjeta_chef.js", "r", encoding="utf-8") as f:
    text = f.read()

# Reemplazar el texto del progreso
# text to find: `<div class="asian-flash-progress-text">${porcentaje}% VENDIDO</div>`
# text to replace: 
# let textoVendido = `${Math.round(vendidosReales)} ${unidadProducto(item) === 'kilo' ? 'KILOS' : 'UNIDADES'} VENDIDOS`;
# Wait, I need to do this cleanly.

replacement = r'<div class="asian-flash-progress-text">${Math.round(vendidosReales)} ${unidadProducto(item) === "kilo" ? "KILOS" : "UNID."}</div>'

text = re.sub(r'<div class="asian-flash-progress-text">\$\{porcentaje\}%\s+VENDIDO</div>', replacement, text)

with open("src/carteleria/lanzador_tv/la_cara_web/modules/columna4/tarjetas/tarjeta_chef.js", "w", encoding="utf-8", newline="") as f:
    f.write(text)
