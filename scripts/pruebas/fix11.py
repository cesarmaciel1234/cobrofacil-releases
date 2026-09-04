import re

with open("src/carteleria/lanzador_tv/la_cara_web/css/themes/premium/estilos.css", "r", encoding="utf-8") as f:
    text = f.read()

replacement = """
/* Etiqueta micro para el carrusel superior (Sellado) */
body[data-theme="premium"] .hero-section .deal-stage__off {
    bottom: auto !important;
    left: auto !important;
    top: -2px !important;
    right: -2px !important;
    font-size: clamp(12px, 1cqw, 14px) !important;
    padding: 3px 8px !important;
    border-radius: 0 12px 0 8px !important;
    transform: scale(1) !important;
"""

text = re.sub(r'/\*\s*Etiqueta micro para el carrusel superior \(Sellado\)\s*\*/\s*body\[data-theme="premium"\] \.hero-section \.deal-stage__off \{.*?transform:\s*scale\([^)]+\)\s*!important;', replacement, text, flags=re.DOTALL)

with open("src/carteleria/lanzador_tv/la_cara_web/css/themes/premium/estilos.css", "w", encoding="utf-8", newline="") as f:
    f.write(text)
