import re
with open('src/jefe/promedios/promedio_ui/vista_promedios.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('for c in range(9):', 'for c in range(11):')

with open('src/jefe/promedios/promedio_ui/vista_promedios.py', 'w', encoding='utf-8') as f:
    f.write(content)
