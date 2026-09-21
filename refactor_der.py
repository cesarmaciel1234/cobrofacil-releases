path_der = 'src/admin/nexus_admin/vistas/componentes/nexus_panel_der.py'
with open(path_der, 'r', encoding='utf-8') as f:
    code = f.read()

import re

# We will just patch the execute_query lines to use CerebroNexus
code = code.replace(
    'self.total_logs_count = db_manager.execute_scalar(q_count, tuple(p)) or 0',
    '''from src.cerebro_global.nexus_cerebro import CerebroNexus
            self.total_logs_count = CerebroNexus.ejecutar_escalar(q_count, tuple(p)) or 0'''
)
code = code.replace(
    'page_logs = db_manager.execute_query(q_paginated, tuple(self.active_params)) or []',
    '''from src.cerebro_global.nexus_cerebro import CerebroNexus
            page_logs = CerebroNexus.ejecutar_query(q_paginated, tuple(self.active_params)) or []'''
)
code = code.replace(
    'all_matching_logs = db_manager.execute_query(self.active_query, tuple(self.active_params)) or []',
    '''from src.cerebro_global.nexus_cerebro import CerebroNexus
            all_matching_logs = CerebroNexus.ejecutar_query(self.active_query, tuple(self.active_params)) or []'''
)

code = code.replace(
    'cierres = db_manager.execute_query("""',
    '''from src.cerebro_global.nexus_cerebro import CerebroNexus
            cierres = CerebroNexus.ejecutar_query("""'''
)

code = code.replace(
    'fechas = db_manager.execute_query("SELECT DISTINCT DATE(fecha) as d FROM cortes_z ORDER BY d DESC")',
    '''from src.cerebro_global.nexus_cerebro import CerebroNexus
        fechas = CerebroNexus.ejecutar_query("SELECT DISTINCT DATE(fecha) as d FROM movimientos_caja WHERE tipo='CIERRE_Z' ORDER BY d DESC")'''
)

# Fix apply theme
new_func = '''    def update_theme(self, theme):
        bg = "#1E293B" if theme == "dark" else "white"
        border = "#334155" if theme == "dark" else "#E2E8F0"
        text = "#F8FAFC" if theme == "dark" else "#0F172A"
        header_bg = "#0F172A" if theme == "dark" else "#F8FAFC"
        
        table_css = f"""
            QTableWidget {{ background-color: {bg}; color: {text}; border: 1px solid {border}; border-radius: 8px; gridline-color: {border}; font-size: 11px; }}
            QHeaderView::section {{ background-color: {header_bg}; color: {text}; font-weight: bold; border: none; border-bottom: 1px solid {border}; padding: 8px; font-size: 10px; }}
            QTableWidget::item:selected {{ background-color: {'#3B82F6' if theme == 'dark' else '#BFDBFE'}; color: {'white' if theme == 'dark' else '#1E3A8A'}; }}
        """
        if hasattr(self, 'tabla_auditoria'):
            self.tabla_auditoria.setStyleSheet(table_css)
        if hasattr(self, 'tabla_cierres'):
            self.tabla_cierres.setStyleSheet(table_css)
'''

pattern = re.compile(r'    def aplicar_tema.*?pass', re.DOTALL)
if pattern.search(code):
    code = pattern.sub(new_func, code)
else:
    code += '\n' + new_func

with open(path_der, 'w', encoding='utf-8') as f:
    f.write(code)

# Add ejecutar_query and ejecutar_escalar to CerebroNexus
path_cer = 'src/cerebro_global/nexus_cerebro.py'
with open(path_cer, 'r', encoding='utf-8') as f:
    code_cer = f.read()

new_db_funcs = '''
    @staticmethod
    def ejecutar_query(q, p):
        from src.base_de_datos.database import db_manager
        return db_manager.execute_query(q, p)

    @staticmethod
    def ejecutar_escalar(q, p):
        from src.base_de_datos.database import db_manager
        return db_manager.execute_scalar(q, p)
'''
code_cer += new_db_funcs
with open(path_cer, 'w', encoding='utf-8') as f:
    f.write(code_cer)
