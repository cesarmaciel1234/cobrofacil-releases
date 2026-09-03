import re

# Fix tarjeta_chef.js
with open('src/carteleria/lanzador_tv/la_cara_web/modules/columna4/tarjetas/tarjeta_chef.js', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(r'<div style=\"color: #000;[^\>]+>\$\{escapeHtml\(textoValidezOferta\(item\)\)\}<\/div>',
              '<div class=\"asian-flash-condition\"></div>', text)

with open('src/carteleria/lanzador_tv/la_cara_web/modules/columna4/tarjetas/tarjeta_chef.js', 'w', encoding='utf-8', newline='') as f:
    f.write(text)

# Fix columna4_chef.css
with open('src/carteleria/lanzador_tv/la_cara_web/css/columna4_chef.css', 'r', encoding='utf-8') as f:
    css = f.read()

# Replace .asian-flash-prices with a clean style
css = re.sub(r'\.asian-flash-prices\s*\{[^}]+\}', '.asian-flash-prices {\n    display: flex;\n    align-items: baseline;\n    gap: 0.5vw;\n    margin-bottom: 0.5vh;\n}', css)
# Replace .asian-flash-current 
css = re.sub(r'\.asian-flash-current\s*\{[^}]+\}', '.asian-flash-current {\n    color: #FFDF00 !important;\n    font-size: clamp(2rem, 3.5vw, 3rem) !important;\n    font-weight: 800 !important;\n    line-height: 1 !important;\n}', css)
# Replace .asian-flash-original
css = re.sub(r'\.asian-flash-original\s*\{[^}]+\}', '.asian-flash-original {\n    color: #888888 !important;\n    font-size: clamp(1.1rem, 1.6vw, 1.4rem) !important;\n    text-decoration: line-through !important;\n    margin-right: 1vw !important;\n    font-weight: 500 !important;\n}', css)

with open('src/carteleria/lanzador_tv/la_cara_web/css/columna4_chef.css', 'w', encoding='utf-8', newline='') as f:
    f.write(css)

