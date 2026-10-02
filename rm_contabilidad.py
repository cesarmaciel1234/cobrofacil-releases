import re

file_path = 'src/admin/dashboard/dashboard_main.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('"nexus_pro", "contabilidad", "proveedores", "red_lan", "cierre"', '"nexus_pro", "proveedores", "red_lan", "cierre"')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)

file_path_jefe0 = 'src/jefe/jefe0_dashboard.py'
with open(file_path_jefe0, 'r', encoding='utf-8') as f:
    text_jefe0 = f.read()

pattern = r'\(\s*"contabilidad"\s*,.*?None\s*\),'
text_jefe0 = re.sub(pattern, '', text_jefe0, flags=re.DOTALL)

with open(file_path_jefe0, 'w', encoding='utf-8') as f:
    f.write(text_jefe0)
print('Removed contabilidad')
