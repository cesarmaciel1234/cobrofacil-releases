import codecs
import re

path_cen = 'src/admin/nexus_admin/vistas/componentes/nexus_panel_cen.py'
with codecs.open(path_cen, 'r', 'utf-8') as f:
    cen = f.read()

# I will use unicode escapes to bypass powershell messing with literal emojis
cen = re.sub(r'icon = .*?role', 'icon = "\U0001F6D2" if "CAJA" in role else "\U0001F4FA" if "CARTEL" in role else "\U0001F4BB" if "ADMIN" in role else "\u2699\uFE0F"', cen)
cen = re.sub(r'\?\? NEXUS GLOBAL DATABASE', '\U0001F4E1 NEXUS GLOBAL DATABASE', cen)
cen = re.sub(r'\?\? VER TODA LA RED', '\U0001F310 VER TODA LA RED', cen)
cen = re.sub(r'\?\? ONLINE', '\u25CF ONLINE', cen)
cen = re.sub(r'\?\? OFFLINE', '\u25CB OFFLINE', cen)
cen = re.sub(r'\?\? SELECTED', '\u25CF SELECTED', cen)
cen = re.sub(r'CyberMetric\("EFECTIVO CASH", "\?\?"\)', 'CyberMetric("EFECTIVO CASH", "\U0001F4B5")', cen)
cen = re.sub(r'CyberMetric\("VENTAS DIGITALES", "\?\?"\)', 'CyberMetric("VENTAS DIGITALES", "\U0001F4B3")', cen)
cen = re.sub(r'CyberMetric\("FONDO INICIAL", "\?\?"\)', 'CyberMetric("FONDO INICIAL", "\U0001F4B0")', cen)

# In case they were just '?'
cen = re.sub(r'\? NEXUS GLOBAL DATABASE', '\U0001F4E1 NEXUS GLOBAL DATABASE', cen)
cen = re.sub(r'\? VER TODA LA RED', '\U0001F310 VER TODA LA RED', cen)
cen = re.sub(r'\? ONLINE', '\u25CF ONLINE', cen)
cen = re.sub(r'\? OFFLINE', '\u25CB OFFLINE', cen)
cen = re.sub(r'\? SELECTED', '\u25CF SELECTED', cen)
cen = re.sub(r'CyberMetric\("EFECTIVO CASH", "\?"\)', 'CyberMetric("EFECTIVO CASH", "\U0001F4B5")', cen)
cen = re.sub(r'CyberMetric\("VENTAS DIGITALES", "\?"\)', 'CyberMetric("VENTAS DIGITALES", "\U0001F4B3")', cen)
cen = re.sub(r'CyberMetric\("FONDO INICIAL", "\?"\)', 'CyberMetric("FONDO INICIAL", "\U0001F4B0")', cen)

with codecs.open(path_cen, 'w', 'utf-8') as f:
    f.write(cen)

path_izq = 'src/admin/nexus_admin/vistas/componentes/nexus_panel_izq.py'
with codecs.open(path_izq, 'r', 'utf-8') as f:
    izq = f.read()

izq = re.sub(r'\?\?? TERMINAL SYS.OP', '\U0001F4BB TERMINAL SYS.OP', izq)
izq = re.sub(r'\?\?? TOPOLOGIA DE RED', '\U0001F4E1 TOPOLOGIA DE RED', izq)

with codecs.open(path_izq, 'w', 'utf-8') as f:
    f.write(izq)
