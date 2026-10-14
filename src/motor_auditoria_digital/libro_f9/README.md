# Libro F9

Qué hace: guarda qué ticket se cerró con F9 (cobro manual).

Qué función: `anotar(ticket, monto, metodo)`, `lista()`, `hay(ticket)` en `libro.py`.

Cómo funciona: `anotar` escribe `reportes/f9_manuales.json` en un hilo daemon. El cobro (`post_cobro`) ya corre en otro hilo: si el disco falla, la venta igual quedó.

Qué devuelve cuando falla: no lanza. `lista()` → `{}`.

Qué no debe cambiar: no esperar este archivo para cerrar la venta. No pedir PIN.
