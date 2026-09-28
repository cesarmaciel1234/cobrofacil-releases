# huella — ID único y auditoría de clientes

Cada cliente nace con un `uid` que dice dónde y cuándo: `NOMBREPC-XXXX-AAAAMMDDhhmmss-hex`. Cada cambio es un evento en `clientes_auditoria` con su propio ID. La tienda (MariaDB de la maestra) toma sola lo que se hizo sin red.

## Piezas

- `pc.py`: `pc_id()` (nombre de Windows + 4 letras de `MachineGuid`; `config.pc_id` lo fija a mano), `usuario()`, `caja()`, `nuevo_uid()`, `nuevo_evento()` (ordenable: microsegundos + contador).
- `tabla.py`: `asegurar(db)` agrega a `clientes` las columnas `uid`, `origen_pc`, `creado_por`, `creado_en`, `actualizado_en`, el índice único `ux_clientes_uid` y la tabla `clientes_auditoria`. Una vez por base y proceso. En la tienda, `completar_uids` pone `TIENDA-<id>` al cliente sin huella. Devuelve False si la base no deja (y el alta sigue como siempre).
- `eventos.py`:
  - `alta(campos, via)`: INSERT con huella + evento `ALTA`. La usan `ClienteRepository` (fiado express, cuenta corriente) y `MotorCuenta.alta_regular` (cartera).
  - `editar(id, cambios, accion)`: UPDATE + `actualizado_en` + evento con `antes` / `despues` de lo que cambió. Nunca toca `deuda_actual`.
  - `movimiento_en(cursor, 'CARGO'|'ABONO', ...)`: dentro de la transacción de `cargar_manual` / `abonar`, con SAVEPOINT. Si el libro falla, el movimiento igual entra.
- `absorber.py`: la tienda aplica eventos hechos sin red (`base = 'LOCAL'`).
- `consulta.py`: `listar(texto)` y `huella_texto(cliente)` para la cartera. Solo lee.

## Cómo viaja

1. Sin red (casa o notebook), `db_manager` es el SQLite local: el evento queda con `base = 'LOCAL'`.
2. El hilo `arrancar()` (cada 120 s, desde `main.py`):
   - sin red y con nodo en `jefe_nodo_path`: `llevar_al_nodo` copia los eventos al pendrive;
   - con red: `aplicar` los eventos del `punpro.db` de esta PC (solo los de su `pc_id`) y los del nodo.
3. `sincronizar_faltantes` del nodo también los toma antes de actualizar el espejo.

Si la maestra contesta pero tiene tablas dañadas (`espejo.copia.tienda_rota()`), el turno no hace nada y lo anota en `estado()`: no intenta el ALTER cada vuelta.

## Reglas de `aplicar_evento`

Una transacción por evento: primero entra la fila en `clientes_auditoria` (clave = ID del evento). Si ya estaba (clave repetida: 1062 / UNIQUE), `repetido` y no hace nada. Dos PCs a la vez: la segunda choca y no aplica. Cualquier otro error es `error` y se reintenta en la vuelta siguiente.

- `ALTA`: si el `uid` no existe, busca gemelo (mismo DNI, o sin DNI y mismo nombre). Si hay, anota `FUSION` y los eventos de ese `uid` van a ese cliente. Si no, crea el cliente con deuda 0 y la huella de origen.
- `EDICION` / `LIMITE`: aplica `despues` solo si la tienda no editó la ficha después (`actualizado_en`). Si no, queda `llego_via = 'NODO:TIENDA_MAS_NUEVA'`.
- `CARGO` / `ABONO`: mueve la deuda y escribe `cuenta_corriente` con «cargado en PC por usuario el fecha». El abono no baja de cero.
- Cliente que todavía no llegó: `pendiente`, no se marca, se reintenta.

## Qué no cambiar

- No copiar fichas ni saldos de afuera: solo eventos. La deuda de una venta fiada sin red viaja con la venta (cola offline); si el absorbedor la copiara, se contaría dos veces.
- El nodo se lee con `sqlite3`, no con `db_manager`.
- Sin las columnas (`asegurar` en False), el alta de clientes sigue funcionando sin huella.
