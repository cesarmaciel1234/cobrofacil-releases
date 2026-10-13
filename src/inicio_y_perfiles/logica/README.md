# Lógica de inicio

`AuthController.listar_credenciales` lee usuarios al abrir el login. `authenticate` compara el hash en memoria: Enter no espera a la maestra. Si Enter vuelve a tardar, no metas una segunda query a `usuarios`; ver `src/cajero/paso6_cobro/reparacion.md`.

`caja_controller.py` abre la caja del turno. No pinta la ventana.
