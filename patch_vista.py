import re
file_path = 'src/contabilidad/vista_resumen.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

pattern = r"self\._btn_resumen_reload = btn_primary\((.*?)\)\n\s+self\._btn_resumen_reload\.clicked\.connect\(self\._load_resumen\)\n\s+hdr\.addWidget\(self\._btn_resumen_reload\)"

replacement = '''self._btn_resumen_reload = btn_primary(\\1)
        self._btn_resumen_reload.clicked.connect(self._load_resumen)
        
        self._btn_sync_tpv = btn_primary("📥 Importar TPV (Hoy)")
        self._btn_sync_tpv.setStyleSheet(f"""
            QPushButton {{
                background-color: {PAL['success']};
                color: {PAL['text2']};
                border: none; border-radius: 8px;
                padding: 10px 20px; font-weight: 700; font-size: 14px;
            }}
            QPushButton:hover {{ background-color: {PAL['success_hover']}; }}
        """)
        self._btn_sync_tpv.clicked.connect(self._sync_ventas_tpv)
        
        hdr.addWidget(self._btn_sync_tpv)
        hdr.addWidget(self._btn_resumen_reload)'''

text = re.sub(pattern, replacement, text, flags=re.DOTALL)

method = '''
    def _sync_ventas_tpv(self):
        try:
            from src.contabilidad.integracion_maestra.sincronizador import SincronizadorMaestra
            sinc = SincronizadorMaestra(self.db)
            exito = sinc.traer_ventas_del_dia()
            if exito:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Éxito", "Las ventas del TPV de hoy se sincronizaron con éxito en Ingresos.")
                self._load_resumen()
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Aviso", "No hay ventas hoy o falló la conexión con la base maestra.")
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Ocurrió un error: {e}")
'''

text += method

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)

print('Boton Sincronizador agregado con exito.')
