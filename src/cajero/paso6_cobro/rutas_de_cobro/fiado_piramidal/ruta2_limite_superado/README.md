# Ruta 2: Límite Superado

## Qué hace
Gestiona el bloqueo por exceso de límite de crédito (`panel_bloqueo.py`), permitiendo validar PIN de supervisor o derivar la cuenta al Módulo de Cobranza.

## Funciones principales
- `panel_bloqueo.py`:
  - Informa el exceso de margen y permite solicitar PIN de supervisor o saltar a Cobranza.
  - `solicita_cobranza`: Emite solicitud para abrir el centro de liquidación.

## Cómo funciona
Si un cliente no posee margen disponible suficiente para cubrir el carrito, el sistema muestra la pantalla roja de bloqueo:
- El supervisor puede ingresar su PIN de 4 dígitos para conceder una excepción puntual.
- Alternativamente, se puede derivar al **Módulo de Cobranza** para liquidar deuda previa y liberar disponible.


