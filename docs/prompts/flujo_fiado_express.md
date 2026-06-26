# Prompt — Fiado Express DNI + creación al vuelo

> Actúa como experto en Python, PyQt6 y MariaDB. Implementa **DialogoFiadoExpress** (ventana negra terminal):
> 1. Monto autocompletado (`self.total_final` desde paso6).
> 2. Enter en DNI → `ClienteRepository.verificar_y_crear_cliente(dni)` con parámetros SQL.
> 3. Si existe: muestra nombre. Si no: INSERT `Express [DNI]`, `tipo_cliente='express'`.
> 4. Bloquea confirmación solo si crédito insuficiente; aviso ámbar si deuda >80% límite.
> 5. Confirmar → `accept()` → paso6 `finalizar()` + cuenta corriente MariaDB.

**Implementado:** `fiado_express.py`, `cliente_repository.py`, migración `clientes.dni` + `tipo_cliente`.

**Límite Express default:** $20.000 (`FIADO_EXPRESS_LIMITE_DEFAULT` / `config.fiado_express_limite`).

**Alarma:** triple beep + borde rojo si la venta supera el cupo. Admin amplía límite en Clientes → botón **Límite**.
