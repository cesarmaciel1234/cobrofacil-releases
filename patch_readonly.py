import re
with open('src/jefe/promedios/promedio_ui/vista_promedios.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('if c in [2, 7, 8]:', 'if c in [2, 7, 8, 9, 10]:')

with open('src/jefe/promedios/promedio_ui/vista_promedios.py', 'w', encoding='utf-8') as f:
    f.write(content)
