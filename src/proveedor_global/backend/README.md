# Backend - Motor Proveedor y Servicios de Abastecimiento

Esta subcarpeta contiene la lógica de negocio y las reglas de acceso a la base de datos para la gestión de proveedores, compras y recepción de mercadería.

- **Qué hace:** Provee `MotorProveedor`, `FichaProveedor` (`ficha.py`) y `RecepcionService` (`recepcion_service.py`).
- **Qué funciones:** 
  - `ficha.py`: `FichaProveedor.crear` da de alta la ficha en la maestra (`P00012`), `FichaProveedor.listar` lee las fichas activas asegurando la tabla.
  - `recepcion_service.py`: `RecepcionService.buscar_producto_por_escaneo` parsea multiplicadores (`7*codigo`) y busca en `productos`. `RecepcionService.procesar_ingreso_mercaderia` abre una conexión, inserta el remito, suma `stock + ?`, guarda ítems y gasto, y confirma todo junto. El id del remito es `lastrowid`. Si algo falla, hace rollback. El aviso a la planilla va después: si falla, el ingreso queda.
  - `motor_proveedor.py`: `save_proveedor` inserta el romaneo pesable y desposte; `pagar_proveedor` salda deudas en gastos; `load_proveedores` arma el historial. El asiento usa `contable()`.
  - `moneda.py`: `texto` pinta el monto, `leer` lo vuelve número, `codigo` y `simbolo` salen de la config.
- **Cómo funciona:** Opera sobre la base de datos de la tienda (db_manager), ejecutando sentencias parametrizadas seguras.
- **Qué devuelve cuando falla:** Lanza `RuntimeError` o retorna `(False, motivo, {})` con el detalle descriptivo.
- **Qué no debe cambiar una mejora futura:** No aislar la lectura/escritura por perfil. Las recepciones de mercadería y compras son globales. El incremento de stock debe ser estrictamente acumulativo (`stock + ?`). No guardar el código `P00012` en lugar del nombre en deudas históricas.
