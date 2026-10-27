# Reportes Historial (Jefe)


### Modificaciones Recientes (Vistas y Filtros)
- **Grilla reordenada:** Las columnas se ajustaron con anchos específicos y Stretch para evitar recortes (Orden: Folio, Caja, Arts, Hora, Total, Extra, Cliente, Estado).
- **Detalle de Venta:** Agregada la columna "Precio".
- **Integración de Notas:** Se lee 
otas_manager. Si el ticket tiene nota, la grilla se marca en naranja oscuro y aparece un botón dinámico 📝 Nota para auditar lo que escribió el cajero.
- **Filtros Adicionales:** El combobox incluye "REDONDEO" y "RECARGO". El filtrado se intercepta y resuelve en src.historial_ventas.listar.
- **Día o mes:** El combo de la fecha elige el día o el mes de esa fecha. «Todas las fechas» suelta los dos.
- **Desglose imprimible:** El botón Desglose de artículos junta las ventas cerradas del filtro. La cantidad de cada nombre dice `kg` o `un`. Imprimir manda `ticket_volumen` a la tiketera, al ancho configurado, para llevar el volumen en la billetera. El pie muestra la plata, los kilos, las unidades y la cantidad de nombres.
