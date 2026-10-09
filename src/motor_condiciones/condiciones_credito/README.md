# Submotor: Condiciones de Crédito

## ¿Qué hace?
Genera los mensajes y condiciones legales relacionados con operaciones de crédito.

## ¿Qué función cumple?
Cubre escenarios como "Venta a Crédito" (pagarés), "Abono de Deuda" (saldos actualizados) y "Estado de Cuenta".

## ¿Cómo funciona?
Implementa `generar_texto(subcontexto, saldo_anterior, monto_actual, **kwargs)`. Basado en el subcontexto, formatea y devuelve una cadena de texto lista para impresión.
