# Cobranza (F6 del paso 5)

La nota de la rama es `punta del piramide.md`. Solo cobra fiado y cuenta corriente **en el paso 5**. F6 abre `dialogo.py` (`DialogoCentroCobranzas`). No es el botón COBRANZA del paso 6. Tabla: `src/cajero/README.md`. No crea clientes: eso es crédito del paso 6. No mete ni saca efectivo suelto (F2 entra, F5 sale). `consulta.buscar_cuentas` lista quien ya tiene deuda o saldo a favor. La lista muestra nombre y DNI; oculta importes hasta elegir. PAGAR/ABONAR abre los medios (Efectivo, Tarjeta, QR, Transferencia, Mixto) en `ui_selector`. PIN y asiento van por `MotorCobranzaMedios`. No abre la venta. Colores en `paleta.py`.

## Seguridad para gran empresa

- **Búsqueda por nombre limitada**: Cuando se busca por nombre, se muestran máximo 5 resultados. Si hay más, se indica al cajero que refine la búsqueda usando DNI o teléfono. Esto evita exposiciones masivas de datos en pantallas públicas.
- **Deudas ocultas en lista**: La lista de resultados no muestra montos de deuda por seguridad. Solo se revela la deuda al seleccionar un cliente específico.
- **Saldo flexible**: Se puede cobrar sin deuda pendiente. El excedente queda a favor. No hay cartel de confirmación.
- **Timer de búsqueda optimizado**: 200ms para balancear velocidad y rendimiento en bases de datos grandes.

Al elegir cliente, un hilo propio (`consulta_historial/`) lee cargos, abonos, BORRADO y CANCELADO. No usa el hilo de admin. Si falla, la cobranza sigue.

`IMPRIMIR RESUMEN` imprime el estado de la cuenta. Al volver al paso 5 o a Admin, el mensajero es el del abono asentado. PIN de cobranza apagado.

Mixto de F6 = abono. Mixto del paso 6 = venta. Admin Abonar usa F6, no el paso 6.
