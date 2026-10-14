# Teclado numérico

Teclas del cobro. Emite `key_clicked`. No valida el monto.

Debajo de Salir y Enter, F10 dice «imprime ticket» y, abajo, «fiscal». `mostrar_fiscal` lo deja azul si AFIP está activo y gris si está apagado. El botón no se esconde. Si todavía se espera el pago, el clic no cierra: deja el ticket fiscal para cuando pague. Si AFIP está apagado, el cartel lo dice y no cambia el cierre. Debajo, si **no hay internet** (TPV rojo), un rótulo dice «F9 sin internet». Con red, QR / tarjeta / transferencia cierran solos y F9 no fuerza el cobro. Ver `paso6_cobro/decisiones.md`.
