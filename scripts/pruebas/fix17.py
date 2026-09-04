import re

with open("src/carteleria/lanzador_tv/la_cara_web/css/themes/premium/estilos.css", "r", encoding="utf-8") as f:
    text = f.read()

# Buscamos .xsell-item__price y .xsell-item__rule y les quitamos background y border.
replacement = """
.xsell-item__price {
    color: var(--accent-primary);
    background: transparent;
    border: none;
}
.xsell-item__rule  { color: var(--accent-primary); background: transparent; }
"""

text = re.sub(r'\.xsell-item__price\s*\{[^}]+\}\s*\.xsell-item__rule\s*\{\s*color:\s*var\(--accent-primary\);\s*background:\s*[^}]+\}', replacement, text, flags=re.DOTALL)

with open("src/carteleria/lanzador_tv/la_cara_web/css/themes/premium/estilos.css", "w", encoding="utf-8", newline="") as f:
    f.write(text)
