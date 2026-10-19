# Historial de Ventas (Lógica Base)


### Novedades
- **notas_manager.py**: Mini-módulo para persistir notas/observaciones de tickets en una base local aislada (
otas_tickets.sqlite) sin romper el esquema ni la sincronización de la BDD principal.
- **listar.py (Filtros)**: Se añadieron lógicas condicionales para "REDONDEO" y "RECARGO", calculando los importes > 0 al vuelo en vez de ser un método de pago.
- **acciones.reimprimir**: Importa `controller` de `caja.py` antes de pedir la copia. Es el botón Imprimir copia del historial del jefe.
