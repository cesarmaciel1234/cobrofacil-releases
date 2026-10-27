# Plano del Módulo: Motor de Abastecimiento Automático (`src/motor_abastecimiento`)

Este módulo implementa el cálculo inteligente de reposición de mercadería por Punto de Reorden (Stock Mínimo y Stock Máximo). Detecta automáticamente qué artículos están en quiebre, calcula la cantidad óptima a comprar y los agrupa por proveedor listos para pedir por WhatsApp, sin interferir con el inventario ni con el cajero.

---

## 🖥️ Frente (Lo que ve el usuario)

1. **Pantalla de Reposición Sugerida:**
   * **Acceso:** Desde el Administrador o panel de Compras / Proveedores.
   * **Qué pinta:**
     * Tarjetas o lista con los proveedores que tienen mercadería pendiente de reponer.
     * Contador de productos bajo el stock mínimo y presupuesto estimado en pesos.
     * Lista de artículos con su stock actual, stock mínimo, techo sugerido y cantidad a pedir (`stock_maximo - stock`).
     * Botón **"Copiar para WhatsApp"**: copia al portapapeles el texto del pedido con el formato listo para enviar al distribuidor.
     * Botón de asignación de proveedor: permite enlazar un departamento entero (ej: `LACTEOS`) o un producto individual a un proveedor con su teléfono de pedidos.
   * **Qué no pinta:**
     * No muestra productos que tengan stock saludable (por encima del mínimo).
     * No permite alterar los precios de venta al público desde esta pantalla.

---

## ⚙️ Fondo (Lo que corre internamente)

### Arquitectura en Pirámide
```
src/motor_abastecimiento/
  plano.md                    <-- Este plano (Frente y Fondo)
  motor_abastecimiento.py     <-- Orquestador principal (MotorAbastecimiento)
  __init__.py
  hilo/
    README.md                 <-- Mini motor que solo pregunta
    pregunta.py               <-- preguntar_alarma(): el único que conoce al inventario
    hilo.py                   <-- HiloReposicion: corre fuera de la ventana
  detector/
    README.md                 <-- Documentación del detector
    calculador_quiebre.py     <-- Pide la alarma al hilo y calcula cuánto comprar
  enlace/
    README.md                 <-- Documentación del puente con proveedores
    puente_proveedor.py       <-- Tabla satélite abastecimiento_proveedor_map
  exportador/
    README.md                 <-- Documentación de formatos de salida
    formato_pedido.py         <-- Armado del texto para WhatsApp y resúmenes
```

### Flujo de Ejecución y Orden de Llamadas
1. **Invocación:** Se llama a `MotorAbastecimiento.obtener_resumen_reposicion()`.
2. **Escaneo de faltantes:** `HiloReposicion` espera el pase de `MotorPlanilla` y `preguntar_alarma()` lee `planilla_reposicion`. No reescribe la planilla y no lee `productos`. Si la planilla no contesta, la lista queda vacía.
3. **Cantidad:** ya viene en la planilla. Con techo, hasta el techo. Con piso solo, hasta el piso. Sin ninguno, la fila queda y la cantidad es cero. Este motor no la vuelve a calcular.
4. **Enlace con proveedores:** `asociar_proveedores_a_productos()` consulta `abastecimiento_proveedor_map`. Gana el producto; si no, el departamento. La ficha (`proveedores`, código `P00012`) vive en `src/proveedor_global/backend/ficha.py` y el enlace guarda su id sin tocar `productos`. Si no hay regla, `"SIN PROVEEDOR ASIGNADO"`.
5. **Formateo para WhatsApp:** `src.motor_abastecimiento.exportador.generar_texto_whatsapp()` construye el texto con viñetas, cantidades y pie de confirmación.
6. **Retorno:** Se devuelve el diccionario global listo para renderizar en pantalla o copiar en 1 clic.

---

## 🚫 Qué NO hay que romper en futuras mejoras
1. **Aislamiento total del inventario:** Este módulo opera en **modo solo-lectura (`SELECT`)** sobre la tabla `productos`. Nunca debe ejecutar `UPDATE` o `DELETE` sobre el inventario.
2. **Independencia del cajero:** La ejecución de este motor nunca debe bloquear el hilo del cajero ni demorar la lectura de códigos de barras.
3. **Tolerancia a faltantes:** Si un producto no tiene proveedor asignado, debe agruparse bajo `"SIN PROVEEDOR ASIGNADO"` sin lanzar excepciones.
