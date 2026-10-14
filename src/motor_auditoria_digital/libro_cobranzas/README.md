# Libro de cobranzas digitales

Qué hace: asienta abonos F6 cobrados con QR, tarjeta o transferencia. Sirve para facturar el mes en que **entró la plata**, aunque la venta a fiado haya sido otro mes.

Qué función: `fusionar(filas, avisar=False)`, `listar(desde, hasta)` en `libro.py`. La clave es `cuenta_corriente.id`. El ticket visible es `COB-{id}`.

Cómo funciona: `reportes/cobranzas_digitales.json`. `consultas.cobranzas` pregunta `cuenta_corriente` (ABONO) y fusiona. `MotorCobranzaMedios.finalizar` anota si el medio es digital. El nodo mezcla el archivo. Sin red se lee este libro.

Qué devuelve cuando falla: no lanza. `listar` → `[]`.

Qué no debe cambiar: no escribe `ventas`. No cobra. No espera este archivo para asentar el abono.
