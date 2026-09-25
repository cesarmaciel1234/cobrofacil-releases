# historial/ (cara jefe)

`vista.py` = interfaz clara.  
Motor = `src/historial_ventas/` (todas las cajas).

## Arrancar

- Filtros: día manda; “Todas las fechas” solo suelta el día. Pago / caja / hora / búsqueda siempre valen. El pago incluye FIADO y CLIENTES, las mismas claves que guarda la venta.
- Hoy destilda histórico y filtra el día de hoy.
- Ticket cancelado: mostrar `motor.linea_cancel` (quién, perfil, caja origen, caja que actuó).
- Letras: `letra.py`, peso 400. No importes estilos del cajero.
- No edites `src/cajero/paso8_historial`.

Compat: `../vista_historial.py` reexporta esta vista.
