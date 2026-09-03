import re

with open("src/carteleria/lanzador_tv/la_cara_web/modules/columna4/tarjetas/tarjeta_chef.js", "r", encoding="utf-8") as f:
    text = f.read()

# I need to find the text:
# <div class="asian-flash-progress-text">${mostrarVendido} ${unidadProducto(item) === "kilo" ? "KILOS" : "UNID."}</div>
# And replace it with:
# <div class="asian-flash-progress-text">${mostrarVendido}% VENDIDO</div>

replacement = '<div class="asian-flash-progress-text">${mostrarVendido}% VENDIDO</div>'
text = re.sub(r'<div class="asian-flash-progress-text">\$\{mostrarVendido\} \$\{unidadProducto\(item\) === "kilo" \? "KILOS" : "UNID\."\}</div>', replacement, text)

with open("src/carteleria/lanzador_tv/la_cara_web/modules/columna4/tarjetas/tarjeta_chef.js", "w", encoding="utf-8", newline="") as f:
    f.write(text)
