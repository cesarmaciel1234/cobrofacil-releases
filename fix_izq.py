import codecs
import re

path = 'src/admin/nexus_admin/vistas/componentes/panel_izquierdo/nexus_panel_izq.py'
with codecs.open(path, 'r', 'utf-8') as f:
    code = f.read()

# Fix add_log
code = re.sub(r'def add_log\(self, text\):.*?self\._trim_terminal\(\)', 
'''def add_log(self, text):
        self.terminal_output.append(f"> {text}")
        self.terminal_output.verticalScrollBar().setValue(self.terminal_output.verticalScrollBar().maximum())
        self._trim_terminal()''', code, flags=re.DOTALL)

# Fix add_structured_log
code = re.sub(r'def add_structured_log\(self, titulo.*?self\._trim_terminal\(\)',
'''def add_structured_log(self, titulo, accion, descripcion, color_titulo="#000000", color_accion="#000000"):
        self.terminal_output.append("")
        titulo_html = f'<b style="font-size: 12px;">=== {titulo.upper()} ===</b>'
        self.terminal_output.insertHtml(titulo_html + "<br>")
        self.terminal_output.append("-" * (len(titulo) + 10))
        self.terminal_output.append(f"• {accion}")
        self.terminal_output.append(f"  {descripcion}")
        self.terminal_output.verticalScrollBar().setValue(self.terminal_output.verticalScrollBar().maximum())
        self._trim_terminal()''', code, flags=re.DOTALL)

# Fix inject_ai_log
code = re.sub(r'def inject_ai_log\(self, category.*?self\._trim_terminal\(\)',
'''def inject_ai_log(self, category, origin, message, time_str):
        clean_org = origin.split('|')[-1].upper() if '|' in str(origin) else f"CAJA {origin}"
        
        if category == "VENTA_EFECTIVO": tipo = "VENTA EFECTIVO"; color = None
        elif category == "VENTA_DIGITAL": tipo = "VENTA DIGITAL"; color = None
        elif category == "APERTURA_SOFTWARE": tipo = "APERTURA CAJON (SOFTWARE)"; color = None
        elif category == "APERTURA_HARDWARE_OK": tipo = "APERTURA CAJON (VALIDADO)"; color = None
        elif category == "ALARMA_CRITICA": tipo = "ALERTA CRITICA"; color = "#FF0000"
        elif category == "INTERVENCION": tipo = "INTERVENCION ADMIN"; color = "#FF6600"
        else: tipo = category; color = None

        if color:
            log_html = f'<span style="color: {color}; font-weight: bold;">[{time_str}] [{clean_org}] {tipo}:</span> {message}'
            self.terminal_output.append(log_html)
        else:
            log_text = f"[{time_str}] [{clean_org}] {tipo}: {message}"
            self.terminal_output.append(log_text)
        
        self.terminal_output.append("") # Pequeña separación
        self.terminal_output.verticalScrollBar().setValue(self.terminal_output.verticalScrollBar().maximum())
        self._trim_terminal()''', code, flags=re.DOTALL)

# Fix the duplicate logging of "FILTRO APLICADO" in nexus_controller.py
path_ctrl = 'src/admin/nexus_admin/logica/nexus_controller.py'
with codecs.open(path_ctrl, 'r', 'utf-8') as f:
    ctrl_code = f.read()

ctrl_code = re.sub(
r'    def _on_caja_selected\(self, origen\):\s*self\.current_caja_filter = str\(origen\)\s*if hasattr\(self\.view, \'panel_izq\'\) and hasattr\(self\.view\.panel_izq, \'add_log\'\):\s*self\.view\.panel_izq\.add_log\(f"\[FILTRO APLICADO\] Auditando: \{origen\}"\)',
'''    def _on_caja_selected(self, origen):
        # Evitar spam si se hace clic repetido en el mismo filtro
        is_new_filter = getattr(self, "current_caja_filter", None) != str(origen)
        self.current_caja_filter = str(origen)
        
        if is_new_filter and hasattr(self.view, 'panel_izq') and hasattr(self.view.panel_izq, 'add_log'):
            self.view.panel_izq.add_log(f"[FILTRO APLICADO] Auditando: {origen}")''', ctrl_code)

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(code)

with codecs.open(path_ctrl, 'w', 'utf-8') as f:
    f.write(ctrl_code)

print("Fixed spacing and duplicate filters!")
