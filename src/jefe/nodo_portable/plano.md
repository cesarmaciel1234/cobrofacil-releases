# Plano — nodo portable

El código está en `motor_nodo.py` y `espejo/`.

## Frente

El botón del panel del jefe: la primera vez «Copiar nodo»; después «Sincronizar nodo». El diálogo ofrece Sincronizar, Promover y Reemplazar. No hay «Importar».

Sin red, la vitrina muestra la franja ámbar «Sin red · datos de la tienda al …» y los números salen de la copia.

## Fondo

La maestra es dueña de todo.

1. `espejo/` guarda en esta PC la copia de la tienda. Cuando la maestra contesta, el servidor esclava sube primero la cola y después `refrescar()` baja solo lo que falta (`espejo/README.md`). La bajada es un instante. Si hay un ticket a medio cargar, esa vuelta no se pasa y queda la copia anterior entera. Si pasa, pasa toda en un solo commit. Queda en tres rutas: AppData, `backups\nodo` del programa y `Documentos\CobroFacil_Backups\nodo`. Si se pierde una, se lee la otra. Sin maestra no se toca la copia ni la cola. La esclava baja el `.sql` de quien se anuncia como maestra en ese momento, sin IP fija, a sus tres carpetas de backup (`backups\db`, AppData y Documentos).
2. El pendrive (`nodo_negocio.db`) es una copia de ese archivo. Sincronizar: une primero los archivos del monitor MP (`reportes/mercado_pago_sync.csv` y `reportes/mp_vinculos.json`) por ID de pago para llevar y traer pagos, marcas de omitido/restaurado y asociaciones a tickets. Luego refresca la copia si hay maestra, la tienda toma los eventos de clientes que traía el pendrive (`_chupar_antes`) y, si aplicó alguno, refresca otra vez antes de volcar (`espejo.volcar_a`). Así el saldo (`clientes.deuda_actual`) y los movimientos de `cuenta_corriente` de esos eventos ya quedan en el nodo en la misma vuelta. Después vuelve a poner los eventos hechos sin red que traía (`_devolver_eventos`). Si falla ese segundo refresco, no pisa el archivo anterior del nodo. Sin maestra lleva la última copia buena.
3. Sin maestra, `espejo.fuente()` hace que vitrina, reportes financieros y auditoría lean la copia de esta PC; si no hay (otra PC en casa), la del pendrive.

Viaja toda la tienda: ventas, detalle, movimientos de caja, productos, clientes (con huella), `clientes_auditoria`, `cuenta_corriente`, `mp_pagos` y el resto (usuarios, configuración, categorías, `gastos`, `romaneos`, `romaneo_items`…), con todas sus columnas. `gastos` se relee entera para mantener al día el estado de compras de proveedores. El módulo global de Proveedores puede consultar esas compras sin red; no crea compras ni pagos en la copia. Menos `terminales_activos`.

4. El mismo pendrive, o la copia de esta PC, sirve para restaurar la tienda: Configuración → Mantenimiento → Respaldo → Importar / Restaurar. Es el motor de `src/base_de_datos/restaurar`, el mismo que usan los respaldos. El jefe copia cada 1 minuto y el `.sql` también; el sello con hora queda cada 30 minutos. De las copias viejas `espejo_tienda_hasta_` quedan diez; la más antigua se borra. El archivo vivo no. Ninguno borra las copias del otro.

Para leer el pendrive hace falta el sistema instalado. La tienda trabaja con MariaDB; el pendrive es un SQLite de viaje y lleva usuarios y configuración: se cuida como una llave.

Clientes cargados afuera: no se importan fichas; los lleva `src/clientes_fiado/oficina/huella` como eventos.

Historial del monitor MP: viaja como archivos separados de `nodo_negocio.db`. Incluye nombres y emails devueltos por Mercado Pago; se trata con la misma reserva que el resto de los datos del nodo.

Promover (si cayó el servidor) importa del nodo a la base local. Los PNG de productos se sincronizan aparte (`Catalogos/png_productos`).

## Qué no cambiar

- No volver a copiar fichas del nodo a la maestra (`ON DUPLICATE KEY UPDATE`): pisa deudas con datos viejos y choca ids.
- No meter la copia de la tienda en `punpro.db`: es la base de vender sin red, con su cola aparte y sus números de ticket.
- El pendrive y la copia se abren con `sqlite3`, no con `db_manager`.
- El diario de AppData no entra en la copia: sus ids locales pueden repetir un ticket que ya subió con otro número.


## Tolerancia a Fallos y Sincronización en Esclava

El nodo jefe (notebook del dueño) funciona como esclava y sincroniza en background cada 1 minuto.
- **Doble Vía (Espejo vs Ruta Externa):** El sistema guarda los datos que chupa de la maestra en una **ruta externa** seleccionada, pero siempre mantiene un **espejo interno** en la carpeta del sistema.
- **Seguridad:** El sistema del jefe *lee del espejo interno*. Si la ruta externa (ej. pendrive) es extraída o eliminada, el sistema no crashea. Al intentar sincronizar manualmente y detectar que la ruta no existe, muestra el mensaje: *"La ruta no existe, elija uno nuevo"* (necesario para volver a tener el backup externo seguro).
- **Indicador Offline:** Al cortarse la red, la interfaz no se congela (la sincronización ocurre en un QThread). El dashboard debe indicar visualmente a qué hora fue la última sincronización exitosa (ej. 🔴 *Sin red - Últimos datos: 14:30 hs*).
