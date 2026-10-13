# Buscador de clientes

Qué hace: Caja de DNI/nombre y hasta 5 sugerencias.

Qué función: `PanelBuscadorClientes`. Señales `texto_cambiado`, `cliente_elegido`, `creacion_solicitada`.

Cómo funciona: Un match: Enter elige. Varios: flecha o hover y Enter. Sin match: Enter pide crear. `aplicar_modo` cambia el título a CRÉDITO o COBRANZA. La consulta la hace el motor en memoria (3 letras, inicio de 1.ª o 2.ª palabra).

Qué no debe cambiar: las 5 filas se reusan. No crear ni borrar widgets en cada tecla. La consulta es del motor. Sin `:hover` ni `enterEvent` que pinte: la flecha se traba. Si se congela, `paso6_cobro/reparacion.md`.
