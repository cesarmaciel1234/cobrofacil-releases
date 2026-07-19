import os

filepath = r"src\jefe\contabilidad\vista_resumen.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# I will find the KPIs array and insert the 5th one.
# kpis = [
#     ("INGRESOS MES",    f"${ing:,.0f}",   PAL["success"], "Ventas y Facturación"),
#     ("OPEX (GASTOS)",   f"${total_gas:,.0f}", PAL["warning"], "Gastos Operativos"),
#     ("GANANCIA NETA",   f"${ganancia_neta:,.0f}", PAL["primary"] if ganancia_neta >= 0 else PAL["danger"], "Bolsillo"),
#     ("FLUJO NETO",      f"${flujo_neto:,.0f}", PAL["success"] if flujo_neto >= 0 else PAL["danger"], "Caja Real"),
# ]

target = '''            kpis = [
                ("INGRESOS MES",    f"${ing:,.0f}",   PAL["success"], "Ventas y Facturación"),
                ("OPEX (GASTOS)",   f"${total_gas:,.0f}", PAL["warning"], "Gastos Operativos"),
                ("GANANCIA NETA",   f"${ganancia_neta:,.0f}", PAL["primary"] if ganancia_neta >= 0 else PAL["danger"], "Bolsillo"),
                ("FLUJO NETO",      f"${flujo_neto:,.0f}", PAL["success"] if flujo_neto >= 0 else PAL["danger"], "Caja Real"),
            ]'''

replacement = '''            drain = self._db.get_daily_drain()
            d_tot = drain.get("total", 0.0)
            
            kpis = [
                ("INGRESOS MES",    f"${ing:,.0f}",   PAL["success"], "Ventas y Facturación"),
                ("SANGRADO DIARIO", f"${d_tot:,.0f}", PAL["danger"], "Provisión Mínima Diaria"),
                ("GANANCIA NETA",   f"${ganancia_neta:,.0f}", PAL["primary"] if ganancia_neta >= 0 else PAL["danger"], "Bolsillo"),
                ("FLUJO NETO",      f"${flujo_neto:,.0f}", PAL["success"] if flujo_neto >= 0 else PAL["danger"], "Caja Real"),
            ]'''

if target in content:
    content = content.replace(target, replacement)
    
    # Also I'll update the tooltip of the KPI to show the breakdown if possible, 
    # but for now let's just update the kpis array.
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("vista_resumen updated with Sangrado Diario KPI")
else:
    print("Could not find kpis array in vista_resumen")
