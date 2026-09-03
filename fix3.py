import re

with open("src/carteleria/lanzador_tv/la_cara_web/css/columna4_chef.css", "r", encoding="utf-8") as f:
    css = f.read()

css += "\n.asian-flash-condition {\n    color: #FFDF00;\n    font-size: clamp(0.9rem, 1.2vw, 1.1rem);\n    font-weight: 600;\n    margin-top: 0.5vh;\n    letter-spacing: 0.03em;\n}\n"

with open("src/carteleria/lanzador_tv/la_cara_web/css/columna4_chef.css", "w", encoding="utf-8", newline="") as f:
    f.write(css)
