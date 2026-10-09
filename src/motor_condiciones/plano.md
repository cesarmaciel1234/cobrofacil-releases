# Plano del Motor de Condiciones

Esta carpeta sigue el modelo de "encarpetado piramidal documentado".

- `motor_central.py`: Fachada principal. Define `MotorCondiciones`. Es el único punto de entrada para los clientes.
- `condiciones_credito/`: Submotor. Lógica para abonos, deudas y estados de cuenta.
- `condiciones_venta/`: Submotor. Lógica para garantías, devoluciones y mensajes de venta.
- `condiciones_cierre/`: Submotor. Lógica para firmas, auditoría y alertas en cortes de caja (X y Z).
