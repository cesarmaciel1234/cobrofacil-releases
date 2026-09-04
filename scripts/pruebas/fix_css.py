import re

with open("src/carteleria/lanzador_tv/la_cara_web/css/carousel.css", "r", encoding="utf-8") as f:
    text = f.read()

replacement = """
.deal-stage {
    flex: 0 0 34%;
    min-width: 86px;
    border-radius: 14px;
    position: relative;
    display: grid;
    place-items: center;
    background: radial-gradient(circle at 50% 20%, #F8FAFC 0%, #CBD5E1 55%, #64748B 100%);
    box-shadow: inset 0 3px 8px rgba(255,255,255,0.8), inset 0 -4px 10px rgba(0,0,0,0.15);
}
"""

text = re.sub(r'\.deal-stage\s*\{[^}]*?overflow:\s*hidden;[^}]*?\}', replacement, text, count=1)

with open("src/carteleria/lanzador_tv/la_cara_web/css/carousel.css", "w", encoding="utf-8", newline="") as f:
    f.write(text)
