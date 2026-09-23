path_cen = 'src/admin/nexus_admin/vistas/componentes/nexus_panel_cen.py'
with open(path_cen, 'r', encoding='utf-8') as f:
    cen = f.read()

cen = cen.replace('icon = "??" if "CAJA" in role else "??" if "CARTEL" in role else "??" if "ADMIN" in role else "??"', 'icon = "??" if "CAJA" in role else "??" if "CARTEL" in role else "??" if "ADMIN" in role else "??"')
cen = cen.replace('"??"', '"?"')
cen = cen.replace('"? ONLINE"', '"? ONLINE"')
cen = cen.replace('"? OFFLINE"', '"? OFFLINE"')
cen = cen.replace('"? SELECTED"', '"? SELECTED"')
cen = cen.replace('?? NEXUS GLOBAL DATABASE', '?? NEXUS GLOBAL DATABASE')
cen = cen.replace('?? VER TODA LA RED', '?? VER TODA LA RED')
cen = cen.replace('CyberMetric("EFECTIVO CASH", "??")', 'CyberMetric("EFECTIVO CASH", "??")')
cen = cen.replace('CyberMetric("VENTAS DIGITALES", "??")', 'CyberMetric("VENTAS DIGITALES", "??")')
cen = cen.replace('CyberMetric("FONDO INICIAL", "??")', 'CyberMetric("FONDO INICIAL", "??")')

with open(path_cen, 'w', encoding='utf-8') as f:
    f.write(cen)

path_izq = 'src/admin/nexus_admin/vistas/componentes/nexus_panel_izq.py'
with open(path_izq, 'r', encoding='utf-8') as f:
    izq = f.read()

izq = izq.replace('?? TERMINAL SYS.OP', '?? TERMINAL SYS.OP')
izq = izq.replace('?? TOPOLOGIA DE RED', '?? TOPOLOGIA DE RED')

with open(path_izq, 'w', encoding='utf-8') as f:
    f.write(izq)
