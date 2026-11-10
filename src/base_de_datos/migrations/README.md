# Migraciones de base de datos

`migrator.py`, clase `MigratorMixin`, crea las tablas que faltan y agrega compatibilidad a las bases SQLite y MariaDB existentes.

Durante `_migrate_db`, la tabla `configuracion` recibe una sola vez la clave `interes_ticket_activado_en`, con `CURRENT_TIMESTAMP` de la base. Esa fecha permite que los cargos fiados ya existentes comiencen a generar interés desde la activación del cambio, nunca desde la fecha de compra anterior.

La migración se ejecuta al iniciar la base y deja el valor persistido. Si no puede leer la hora, registra el error y no sustituye la fecha por una inventada; el motor de abono verificará o creará el marcador dentro de su transacción.

`offline_cancelaciones` es una cola local durable para F3 en una esclava offline. Cartera guarda allí su reversión contable; ventas aporta los movimientos de caja generados localmente en `movimientos_caja_json`. La cartera coordina su aplicación idempotente con la reproducción del estado del ticket, stock y caja. Se elimina solo cuando la maestra confirma ambas partes.

Qué no cambiar: no sobrescribir la clave en cada arranque, no calcularla con el reloj de una caja distinta y no adelantarla a fechas anteriores al despliegue. Eso podría cobrar interés retroactivo.
