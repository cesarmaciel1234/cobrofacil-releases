# Fiado en cobro

Qué hace: Guarda el buscador de clientes que usa `OrquestadorFiadoPiramidal`.

Qué función: `PanelBuscadorClientes` en `ui/buscador_clientes/`.

Cómo funciona: El orquestador conecta `texto_cambiado` al motor de búsqueda y `cliente_elegido` a `_evaluar_cliente`. `aplicar_modo` pinta CRÉDITO o COBRANZA.

Qué no debe cambiar: `panel.py` (`PanelFiadoCobro`) no está en el flujo. No reactivarlo ni su F5.
