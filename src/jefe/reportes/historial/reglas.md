# historial/ (cara jefe)

`vista.py` = interfaz clara.  
Motor = `src/historial_ventas/` (todas las cajas).

## Arrancar

- Filtros: día manda; “Mes” usa el mes de la fecha elegida; “Todas las fechas” suelta el día y el mes. Pago / caja / hora / búsqueda siempre valen. El pago incluye FIADO y CLIENTES, las mismas claves que guarda la venta.
- Desglose: solo ventas cerradas. Imprimir arma un ticket al ancho de `printer_paper_width_mm` (58 mm = 32 columnas, 80 mm = 48). El nombre va en negrita; debajo, letra chica con `kg` o `un`, precio y plata. `Articulos` cuenta nombres. El comercio sale en letra doble arriba y de nuevo al cierre.
- Hoy destilda histórico y filtra el día de hoy.
- Ticket cancelado: mostrar `motor.linea_cancel` (quién, perfil, caja origen, caja que actuó).
- Letras: `letra.py`, peso 400. No importes estilos del cajero.
- No edites `src/cajero/paso8_historial`.

Compat: `../vista_historial.py` reexporta esta vista.
