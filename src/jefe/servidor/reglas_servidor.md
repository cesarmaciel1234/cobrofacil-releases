# Jefe — reglas del servidor

El panel Red LAN decide el puesto **una vez**. Después cada PC arranca sola.

- **MAESTRA:** el lanzador / Win: ON despierta el servidor (también si esta PC es la de cartelería).
- **ESCLAVA** (notebook del dueño): no enciende MariaDB; `db_host` apunta a la tienda.

Tras un corte, no hay que volver a “Buscar” si la IP maestra no cambió.

**Esclava:** jefe, reportes e historial leen la maestra. No el `punpro.db` de esta notebook. Ver `src/base_de_datos/reglas.md`.
