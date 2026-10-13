# UI de fiado en cobro

Qué hace: Piezas visuales. El flujo vivo usa `buscador_clientes/`. `credito_aprobado/` queda para el panel legado.

Qué función: `PanelBuscadorClientes`.

Cómo funciona: El orquestador piramidal instancia el buscador. No instancia `PanelCreditoAprobado`.

Qué no debe cambiar: el buscador no consulta la base.
