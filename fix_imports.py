import os

files = [
    ('src/jefe/promedios/carne/ui_carne.py', 'motor_Carne', 'motor_carne'),
    ('src/jefe/promedios/cerdo/ui_cerdo.py', 'motor_Cerdo', 'motor_cerdo'),
    ('src/jefe/promedios/pollo/ui_pollo.py', 'motor_Pollo', 'motor_pollo')
]

for fpath, old, new in files:
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace(f"from .{old} import", f"from .{new} import")
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
print('Imports fixed.')
