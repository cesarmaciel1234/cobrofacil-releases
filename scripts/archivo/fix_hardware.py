import codecs
import re

path = 'src/main_window.py'
with codecs.open(path, 'r', 'utf-8-sig', errors='ignore') as f:
    code = f.read()

def repl1(m):
    return m.group(0) + '''
        from src.central_red_global.network_engine import get_network_engine
        engine = get_network_engine()
        if engine:
            engine.broadcast("HARDWARE_SENSOR", {"evento": "DRAWER_OPEN"})
'''

# Connect in operational opening
pattern1 = r'    def _on_operational_opening\(self\):\s*from src\.hardware\.cash_drawer import drawer_manager'
if re.search(pattern1, code):
    code = re.sub(pattern1, repl1, code)
    print("Patched _on_operational_opening")

def repl2(m):
    return m.group(0) + '''
        from src.central_red_global.network_engine import get_network_engine
        engine = get_network_engine()
        if engine:
            engine.broadcast("ALERTA_SEGURIDAD", {"mensaje": "[CRITICO] CAJON FORZADO / INTRUSION DETECTADA"})
'''

pattern2 = r'    def _on_security_breach\(self\):\s*self\.mostrar_alerta_perimetral\(True, modo="security"\)'
if re.search(pattern2, code):
    code = re.sub(pattern2, repl2, code)
    print("Patched _on_security_breach")

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(code)

