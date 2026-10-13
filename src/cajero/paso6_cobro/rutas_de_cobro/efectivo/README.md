# Proceso efectivo

Qué hace: Aísla el cobro en efectivo.

Qué función: `entrar` / `salir` en `proceso.py`. La UI sigue en `monto_en_cobro/` y el vuelto en `resumen_vuelto`.

Cómo funciona: `entrar` abre la hoja y `set_metodo("Efectivo")`. `salir` limpia el casillero y esconde el vuelto. No toca la base.

Qué no debe cambiar: el redondeo del vuelto sigue en `paso6_cobro.calcular_vuelto`.
