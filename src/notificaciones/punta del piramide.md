# Punta de la pirámide — notificaciones

Módulo autónomo. El cajero solo lo muestra. Si el motor se rompe, no hay franja y la venta sigue.

```
src/notificaciones/
  punta del piramide.md
  motor/                 sin pantalla
    estado.py            anota y retira avisos temporales
    revisar.py           elige un mensaje y las lámparas
  interfaz/              sin reglas
    franja.py            un solo mensaje
    icono.py             lámpara muda, sin montos
    centro.py            pinta lo que devolvió el motor
```

Un solo texto en la franja, y solo si acaba de pasar un cobro. El cajón abierto no escribe ahí: es el punto rojo del cabezal. Urgencia de stock, stock bajo y exceso de dinero se juntan en ese mismo punto. Rojo si alguna es urgente, ámbar si solo conviene retirar o hay stock bajo. Al pasar el mouse sale un aviso con el detalle de todas, incluido el monto. Al sacar el mouse, desaparece.

El exceso de dinero no se escribe. La lámpara va en el cabezal, a la izquierda del nombre del negocio: ámbar si conviene retirar, roja si es urgente. El cliente no ve el monto. El cajero, al pasar el mouse, lee «Retiro de caja» o «Retiro urgente».

El borde verde o rojo del cobro lo pinta el terminal. El texto de ese cobro dura 10 segundos en esta franja.
