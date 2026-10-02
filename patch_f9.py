file_path = 'src/cajero/paso6_cobro/fiado_en_cobro/panel.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

new_method = '''    def procesar_f9(self):
        if self._modo == "cobrando_lienzo":
            actual = self.cont_lienzos.currentWidget()
            if hasattr(actual, "tecla"):
                from PyQt6.QtCore import Qt
                actual.tecla(Qt.Key.Key_F9)
                return True
        return False
'''

if 'def procesar_f9' not in text:
    text = text.replace('    def bloquea_enter(self):', new_method + '\n    def bloquea_enter(self):')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print('Added procesar_f9')

file_path_paso6 = 'src/cajero/paso6_cobro/paso6_cobro.py'
with open(file_path_paso6, 'r', encoding='utf-8') as f:
    text = f.read()

old_emergencia = '''    def _emergencia(self):
        if not getattr(self, "_tpv_listo", False):
            return
        if getattr(self, "stack", None) and self.stack.currentIndex() == 0:
            return
        if getattr(self, "_point_en_curso", False):
            self._emergencia_pendiente = True
            self.espera_point.soltar()
            return
        self._cerrar_manual()'''

new_emergencia = '''    def _emergencia(self):
        if not getattr(self, "_tpv_listo", False):
            return
        if getattr(self, "stack", None) and self.stack.currentIndex() == 0:
            return
            
        if getattr(self, "_fiado_flujo_activo", False):
            if hasattr(self, "panel_fiado") and self.panel_fiado.isVisible():
                if hasattr(self.panel_fiado, "procesar_f9"):
                    if self.panel_fiado.procesar_f9():
                        return # El lienzo absorbió el F9

        if getattr(self, "_point_en_curso", False):
            self._emergencia_pendiente = True
            self.espera_point.soltar()
            return
        self._cerrar_manual()'''

if 'if self.panel_fiado.procesar_f9():' not in text:
    text = text.replace(old_emergencia, new_emergencia)
    with open(file_path_paso6, 'w', encoding='utf-8') as f:
        f.write(text)
    print('Patched _emergencia in Paso6Cobro')
