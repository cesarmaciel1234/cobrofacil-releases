import sys
with open('src/carteleria/pantalla_espia.py', encoding='utf-8') as f:
    c = f.read()

if 'C_THEME' not in c[:200]:
    c = 'from src.carteleria.theme import C_THEME\n' + c

c = c.replace('setStyleSheet("font-family', 'setStyleSheet(f"font-family')

with open('src/carteleria/pantalla_espia.py', 'w', encoding='utf-8') as f:
    f.write(c)
