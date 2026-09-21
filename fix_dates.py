import codecs
import re

path = 'src/admin/nexus_admin/vistas/componentes/panel_derecho/nexus_panel_der.py'
with codecs.open(path, 'r', 'utf-8') as f:
    code = f.read()

pattern = r'        f_val = self\.cmb_fecha\.currentText\(\)\s*if f_val == "Hoy": q \+= " AND DATE\(fecha\) = CURDATE\(\)".*?AND MONTH\(fecha\) = MONTH\(CURDATE\(\)\)"'

replacement = '''        f_val = self.cmb_fecha.currentText()
        from datetime import datetime, timedelta
        hoy = datetime.now()
        
        if f_val == "Hoy":
            q += " AND fecha >= ? AND fecha <= ?"
            p.extend([hoy.strftime("%Y-%m-%d 00:00:00"), hoy.strftime("%Y-%m-%d 23:59:59")])
        elif f_val == "Ayer":
            ayer = hoy - timedelta(days=1)
            q += " AND fecha >= ? AND fecha <= ?"
            p.extend([ayer.strftime("%Y-%m-%d 00:00:00"), ayer.strftime("%Y-%m-%d 23:59:59")])
        elif f_val == "Esta Semana":
            inicio_sem = hoy - timedelta(days=hoy.weekday())
            q += " AND fecha >= ? AND fecha <= ?"
            p.extend([inicio_sem.strftime("%Y-%m-%d 00:00:00"), hoy.strftime("%Y-%m-%d 23:59:59")])
        elif f_val == "Este Mes":
            q += " AND fecha >= ? AND fecha <= ?"
            p.extend([hoy.strftime("%Y-%m-01 00:00:00"), hoy.strftime("%Y-%m-31 23:59:59")])'''

if re.search(pattern, code, re.DOTALL):
    code = re.sub(pattern, replacement, code, flags=re.DOTALL)
    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(code)
    print("Fixed date filtering!")
else:
    print("Pattern not found!")
