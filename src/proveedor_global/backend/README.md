# Backend - Motor Proveedor y Servicios de Abastecimiento

Esta subcarpeta contiene la lógica de negocio y las reglas de acceso a la base de datos para la gestión de proveedores, compras y recepción de mercadería.

- **Qué hace:** Provee `MotorProveedor`, `FichaProveedor` (`ficha.py`) y `RecepcionService` (`recepcion_service.py`).
- **Qué funciones:** 
  - `ficha.py`: `FichaProveedor.crear` da de alta la ficha en la maestra (`P00012`). `actualizar` cambia nombre y teléfono; en casa reescribe la cola y los enlaces. Sin tienda no inventa el id: lo deja en `offline_cambios.json` y `listar` muestra solo el nombre. Al volver a la tienda, la nutrición crea el `P00012`. `RecepcionService.buscar_productos_por_iniciales` lista por el inicio del nombre, por una palabra siguiente (provenzal alicante con «alican») y por código de barras o id. Si recibe departamento, no devuelve los de otro.
  - `recepcion_service.py`: `RecepcionService.buscar_producto_por_escaneo` parsea multiplicadores (`7*codigo`) y busca en `productos`. `RecepcionService.procesar_ingreso_mercaderia` abre una conexión, inserta el remito, suma `stock + ?`, guarda ítems y gasto, y confirma todo junto. El id del remito es `lastrowid`. Si algo falla, hace rollback. El aviso a la planilla va después: si falla, el ingreso queda.
  - `motor_proveedor.py`: `save_proveedor` inserta el romaneo pesable y desposte; `pagar_proveedor` salda deudas en gastos; `load_proveedores` arma el historial con el contado y el fiado; en casa suma los remitos de esta PC. Pagar uno de esos usa `pagar_en_casa`, no el id de la tienda. `save_proveedor` guarda cajas × kilos × precio; sin tienda, `_guardar_compra_en_casa` anota el gasto en esta PC. El asiento usa `contable()`. `_ConexionTienda.execute_non_query` mira `rowcount` del cursor de MariaDB; si el cursor no lo trae, no corta el alta.
  - `cuenta.py`: `registrar_pago` anota medio, fecha y nota. `anular` deja la factura en el historial y resta el stock de esa carga. `listar_pagos` arma el historial. No borra el gasto.
  - `moneda.py`: `texto` pinta el monto, `leer` lo vuelve número, `codigo` y `simbolo` salen de la config.
- **Cómo funciona:** Opera sobre la base de datos de la tienda (db_manager), ejecutando sentencias parametrizadas seguras.
- **Qué devuelve cuando falla:** Lanza `RuntimeError` o retorna `(False, motivo, {})` con el detalle descriptivo.
- **Qué no debe cambiar una mejora futura:** No aislar la lectura/escritura por perfil. Las recepciones de mercadería y compras son globales. El incremento de stock debe ser estrictamente acumulativo (`stock + ?`). No guardar el código `P00012` en lugar del nombre en deudas históricas.
