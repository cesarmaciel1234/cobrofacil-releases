import codecs
import re

path = 'src/admin/nexus_admin/vistas/componentes/panel_derecho/nexus_panel_der.py'
with codecs.open(path, 'r', 'utf-8') as f:
    code = f.read()

pattern = r'        tab = getattr\(self, \'active_tab_index\', 0\).*?if tab == 3 and tipo != "INTERVENCION": return\s*pc_clean = src'

replacement = '''        tab = getattr(self, 'active_tab_index', 0)
        # 0=COBROS, 1=CAJONES, 2=ALERTAS, 3=ACCIONES
        if tab == 0 and tipo != "VENTA":
            return
        if tab == 1 and tipo not in ["APERTURA", "CIERRE_Z"]:
            return
        if tab == 2 and tipo != "ALERTA_SEGURIDAD":
            return
        if tab == 3 and tipo != "INTERVENCION":
            return
        
        pc_clean = src'''

if re.search(pattern, code, re.DOTALL):
    code = re.sub(pattern, replacement, code, flags=re.DOTALL)
    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(code)
    print("Fixed indentation for linter")
else:
    print("Pattern not found")
