# Ruta 3: Cliente Nuevo

## ¿Qué hace?
Es un formulario ultra-rápido para registrar un cliente nuevo desde la misma caja, sin necesidad de ir al módulo administrativo de la oficina.

## ¿Qué función cumple en el negocio?
Fidelización en caliente. Si alguien quiere empezar a comprar a crédito, el cajero puede darlo de alta en menos de 5 segundos, otorgándole automáticamente el límite base predeterminado del comercio (ej. $50,000) y finalizando la venta del carrito en ese mismo acto.

## ¿Cómo funciona?
- **`panel_nuevo.py`**: Pide campos básicos (Nombre, Teléfono).
- Al guardar, se comunica con `cerebro.crear_cliente()` y emite una señal al orquestador para simular que el cliente ya existía, pasando automáticamente a aprobarle la venta del carrito actual (Ruta 1).
