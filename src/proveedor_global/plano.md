# Plano - Proveedor Global

Este módulo centraliza la gestión de Compras, Romaneos y Proveedores. Al ser un módulo transversal, es utilizado directamente por:
- src/admin (Carga de mercadería de la tienda)
- src/contabilidad (Control de deudas de proveedores del Jefe)
- src/carteleria (Consulta rápida de ingresos de mercadería)

## Frente
La interfaz visual vive en rontend/vista_proveedor.py. 
- **Qué ve el usuario:** Un formulario de carga de romaneos (proveedor, tropa, kilos, precios) y un historial (lista de deudas y compras pasadas).
- **Qué pinta y qué no pinta:** Pinta los estados de conexión en rojo si se cae la red. Deshabilita el guardado si el cajero/admin está offline.
- **Botones:** "Guardar" para registrar una compra, y "Pagar" dentro del historial para saldar una deuda pendiente.

## Fondo
Toda la lógica dura vive en ackend/motor_proveedor.py. 
- **Qué función corre:** save_proveedor, load_proveedores, pagar_proveedor.
- **En qué tabla toca:** Lee y escribe en las tablas omaneos, omaneo_items y gastos de la base de datos central de MariaDB (db_manager).
- **Qué no hay que romper:** El módulo está completamente **globalizado**. No se debe reintroducir lógica que separe la lectura/escritura dependiendo del perfil (jefe vs dmin). Todos los perfiles operan sobre las deudas y proveedores de la base de datos principal de la tienda.
