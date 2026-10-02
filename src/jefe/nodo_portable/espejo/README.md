# espejo — copia de la tienda en esta PC

Archivo SQLite en `%LOCALAPPDATA%\CobroFacil_PRO\espejo_tienda\espejo_tienda.db`. No es `punpro.db`: esa es la base de vender sin red y no se mezcla con la historia de la tienda.

## copia.py

- `refrescar()`: con la maestra conectada, lee su MariaDB con una conexión propia (pymysql, sin `db_manager`, nunca cae a SQLite) y escribe en la copia.
  - Copia **toda la tienda**, para que el pendrive sirva para restaurarla (`src/base_de_datos/restaurar`). Las 8 del jefe (`TABLAS_NEGOCIO`) más el resto que liste `information_schema` (usuarios, configuración, categorías, departamentos, combos, gastos, romaneos, cartelería…), cada una con su clave primaria. Queda afuera `terminales_activos` (`NO_COPIAR`): es del momento.
  - Una vez por día, completa. El resto de las vueltas: productos, clientes, `clientes_auditoria`, `mp_pagos` (clave `payment_id`) y `gastos` enteras; ventas nuevas más las de los últimos 3 días (cancelaciones, cierres); detalle, caja y `cuenta_corriente` desde el último id. `gastos` se trae entera porque el estado de pago de un proveedor puede cambiar en una fila vieja. Por eso el saldo actual de cada cliente siempre se actualiza desde la maestra, los movimientos nuevos de deuda se agregan al libro y el estado de proveedores sigue el de la tienda.
  - El resto de las tablas: enteras en cada vuelta. Si una pasa de `GRANDE` (5000) filas y su clave es `id`, desde el último id; enteras en la completa del día. Las que guardan archivos (columna blob, hoy `carteleria_media`) solo en la completa del día.
  - Una tabla sin clave primaria se reemplaza entera cuando la tienda la trae con filas.
  - En `espejo_meta` quedan `tablas` (cuántas) y `completa = 1`. Con eso el motor de restaurar sabe que la copia trae toda la tienda; un pendrive de antes (8 tablas) se muestra como «parcial».
  - Se lee todo antes de escribir. Si la tienda da error (tabla dañada, sin red), la copia queda como estaba.
  - La copia anota de qué servidor viene (`servidor` en `espejo_meta`, sale de `SELECT @@hostname` de MariaDB). Si la PC se conecta a otra maestra (por ejemplo de la de prueba a la del negocio, aunque tenga la misma IP) o la copia no tiene servidor anotado, la copia vieja se guarda aparte y arranca una nueva. Así nunca se mezclan datos de dos maestras.
  - Si la maestra solo cambia de IP, el nombre es el mismo: la copia sigue y no se guarda aparte.
  - Si la tienda tiene menos ventas que la copia (se restauró un respaldo o se recrearon tablas), pasa lo mismo.
  - La copia vieja queda como `espejo_tienda_hasta_AAAAMMDD_HHMMSS.db` en la misma carpeta; no se borra.
  - Toma las columnas que tenga la tienda.
- `arrancar()`: hilo cada 5 minutos. Lo prende el panel del jefe, y `main.py` si la PC ya tiene copia.
- `volcar_a(destino)`: copia entera al pendrive (backup de SQLite, modo DELETE para que se lea en un USB).
- `meta()`: `ultima_copia`, `ultimo_completo`, `origen`, `servidor`, `tablas`, `completa`, en la tabla `espejo_meta`.

## Quién la lee

- El sistema instalado: el panel del jefe (`lector.py`) y Mantenimiento → Respaldo → Restaurar. La tienda trabaja con MariaDB; esta copia es solo el formato de viaje.
- Para volver a tener una tienda desde el pendrive hay que instalar el sistema (con su MariaDB) y restaurar la copia desde ahí.
- La copia lleva usuarios y configuración. Es un SQLite común: cualquier visor de SQLite la abre. El pendrive se cuida como una llave del negocio.

## lector.py

- `copia.tienda_rota()`: motivo si la maestra contesta pero sus tablas dan error de motor (1877 dañada, 1932, 1030…). Cache de 60 s. Con eso, la vitrina lee la copia y el hilo de huella de clientes no intenta el ALTER.
- `fuente()`: con tienda sana, `db_manager`. Sin tienda o con tienda rota, un `Lector` de solo lectura sobre la copia de esta PC (si es esclava) o, si no hay, la del pendrive. Si falla una consulta devuelve `[]`, como `db_manager`.
- `en_copia()`: ruta que se está leyendo, o `''` en vivo.
- `leyenda()`: «Sin red · datos de la tienda al 26/09 21:32 (copia de esta PC)» para la franja ámbar de la vitrina.

La usan los `_db()` de `vitrina/metricas.py`, `reportes/financiero/consulta.py` y `reportes/auditoria/consulta.py`, y `motor_cobros_digitales.veredicto.conciliar.tickets_firmados`.

## Qué no cambiar

- No escribir en `punpro.db` desde acá, ni leer la tienda con `db_manager.execute_query`: se traga los errores y puede cambiar a la base local en medio de la copia.
- No borrar filas de la copia por lo que diga la tienda: solo se agregan o se reemplazan.
- No resolver la deuda por suma/resta de los saldos copiados: el saldo actual viene de `clientes` en la maestra; los movimientos viajan en `cuenta_corriente` o como eventos de huella.
- Los `romaneos` y `romaneo_items` del módulo Proveedores se copian como parte del resto de tablas; `gastos` se copia entera en cada vuelta para traer también cambios de estado en compras viejas. Se leen offline solo como referencia. No registrar en el espejo una compra, un pago ni el desposte.
- No sacar tablas del resto para achicar la copia: sin usuarios ni configuración el pendrive no levanta una tienda.
