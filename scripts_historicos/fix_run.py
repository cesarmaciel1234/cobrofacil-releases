import codecs
import re

with codecs.open('src/jefe/jefe_reportes.py', 'r', encoding='utf-8') as f:
    text = f.read()

match = re.search(r'(    def run\(self\):.*?)(                "SELECT SUM\(dv\.cantidad \* COALESCE\(p\.costo, 0\)\) as costo ")', text, flags=re.DOTALL)
if match:
    correct = """    def run(self):
        try:
            from src.utils.db import db_manager
            # 1. KPIs
            res_kpi = db_manager.execute_query(
                "SELECT SUM(total) as v_bruta, SUM(total - descuento + recargo) as v_neta, COUNT(id) as cant "
                "FROM ventas WHERE (fecha BETWEEN ? AND ?) AND estado IN ('COMPLETADA', 'CERRADA')", 
                (self.start_str, self.end_str)
            )
            v_bruta = float(res_kpi[0]['v_bruta'] or 0.0) if res_kpi and res_kpi[0] else 0.0
            t_cant = int(res_kpi[0]['cant'] or 0) if res_kpi and res_kpi[0] else 0
            
            res_costo = db_manager.execute_query(
"""
    text = text.replace(match.group(1), correct)
    codecs.open('src/jefe/jefe_reportes.py', 'w', encoding='utf-8').write(text)
    print('Fixed run method.')
else:
    print('Regex failed')
