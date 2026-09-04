import re

with open("src/carteleria/lanzador_tv/la_cara_web/css/columna4_chef.css", "r", encoding="utf-8") as f:
    css = f.read()

# Make it absolute bottom left
replacement = """
.asian-flash-product-tag {
    background: rgba(212, 175, 55, 0.2) !important;
    color: #D4AF37 !important;
    border: 1px solid #D4AF37 !important;
    box-shadow: 0 0 10px rgba(212, 175, 55, 0.3) !important;
    position: absolute !important;
    bottom: 10px !important;
    left: 10px !important;
    z-index: 10 !important;
    margin: 0 !important;
}
"""

css = re.sub(r'\.asian-flash-product-tag\s*\{[^}]+\}', replacement, css)

with open("src/carteleria/lanzador_tv/la_cara_web/css/columna4_chef.css", "w", encoding="utf-8", newline="") as f:
    f.write(css)
