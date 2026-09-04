import re

with open("src/carteleria/lanzador_tv/la_cara_web/css/structural_base.css", "r", encoding="utf-8") as f:
    text = f.read()

text = re.sub(r'\.xsell-item__price\s*\{\s*border:\s*1px\s*solid\s*!important;\s*/\*.*?\*/\s*\}', '.xsell-item__price {\n    /* color y background se definirán por el tema */\n}', text, flags=re.DOTALL)

with open("src/carteleria/lanzador_tv/la_cara_web/css/structural_base.css", "w", encoding="utf-8", newline="") as f:
    f.write(text)
