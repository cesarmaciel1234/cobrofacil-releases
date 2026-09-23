import codecs
import re

path = 'src/admin/nexus_admin/vistas/componentes/panel_derecho/nexus_panel_der.py'
with codecs.open(path, 'r', 'utf-8-sig', errors='ignore') as f:
    code = f.read()

pattern = r'    def agregar_log\(self, src, payload, fg_color\):\s*tipo = "EVENTO"\s*if "\[VENTA\]" in payload: tipo = "VENTA".*?if tab == 3 and tipo != "INTERVENCION":\s*return'

replacement = '''    def agregar_log(self, src, payload, fg_color):
        tipo = "EVENTO"
        payload_upper = payload.upper()
        if "[VENTA]" in payload_upper: tipo = "VENTA"
        elif "ALERTA" in payload_upper or "CRITIC" in payload_upper: tipo = "ALERTA_SEGURIDAD"
        elif "INTERVENCION" in payload_upper or "INTERVENCI" in payload_upper: tipo = "INTERVENCION"
        elif "APERTURA" in payload_upper: tipo = "APERTURA"
        elif "CIERRE" in payload_upper: tipo = "CIERRE_Z"
            
        tab = getattr(self, 'active_tab_index', 0)
        # 0=COBROS, 1=CAJONES, 2=ALERTAS, 3=ACCIONES
        if tab == 0 and tipo != "VENTA":
            return
        if tab == 1 and tipo not in ["APERTURA", "CIERRE_Z", "CIERRE_AUTO", "CIERRE_TURNO"]:
            return
        if tab == 2 and tipo != "ALERTA_SEGURIDAD":
            return
        if tab == 3 and tipo != "INTERVENCION":
            return'''

if re.search(pattern, code, re.DOTALL):
    code = re.sub(pattern, replacement, code, flags=re.DOTALL)
    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(code)
    print("Fixed agregar_log!")
else:
    print("Pattern not found!")
