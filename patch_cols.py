import re

with open('src/jefe/promedios/promedio_ui/vista_promedios.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '''self._prom_tabla = build_table(["Corte", "Kilos", "Costo $/kg", "% Ganancia", "Precio/kg Venta", "P. mayoreo", "Cant. may.", "Venta Total", "Ganancia Neta"])''',
    '''self._prom_tabla = build_table(["Corte", "Kilos", "Costo $/kg", "% Ganancia", "Precio Venta", "P. Mayoreo", "C. May.", "V. Total", "Ganancia", "V. Tot. May.", "Gan. May."])'''
)

with open('src/jefe/promedios/promedio_ui/vista_promedios.py', 'w', encoding='utf-8') as f:
    f.write(content)
