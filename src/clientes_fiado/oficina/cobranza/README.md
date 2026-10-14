# Cobranza (oficina)

Consulta de deudores para listados. No es F6.

`consulta.py`: `parse_consulta_cobranza` arma DNI, fecha, monto o nombre. `buscar_deudores` lee `clientes` con `deuda_actual > 0.01` y el último cargo.

Si la consulta falla, devuelve lista vacía. No escribe deuda. F6 usa `f6_centro_cobranzas/consulta.py`, no este archivo.
