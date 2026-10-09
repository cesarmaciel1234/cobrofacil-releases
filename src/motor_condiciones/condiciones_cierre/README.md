# Submotor: Condiciones de Cierre

## ¿Qué hace?
Genera textos de auditoría, firmas requeridas o advertencias para tickets Z y X del cajero o jefe.

## ¿Qué función cumple?
Provee los campos de firma, alertas y validaciones impresas que los empleados deben observar al cerrar un turno o una caja.

## ¿Cómo funciona?
Implementa `generar_texto(subcontexto, usuario, **kwargs)`. Retorna la cadena correspondiente para impresión final de auditoría.
