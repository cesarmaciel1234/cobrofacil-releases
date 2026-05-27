# ✅ CHECKLIST DE PRUEBAS: Cobro Fácil POS

Utilice esta guía para validar que todos los sistemas de seguridad y eficiencia están operando al 100% antes de la puesta en marcha oficial.

---

## 🔒 1. SEGURIDAD DE CAJÓN (ESC/POS)
*   [ ] **Cierre Obligatorio**: Inicie una venta, presione F4 y cobre. El cajón debe abrirse. Intente limpiar la pantalla antes de cerrar el cajón; el sistema **debe bloquear la acción** hasta que el sensor detecte el cierre.
*   [ ] **Alerta Perimetral**: Abra el cajón y manténgalo abierto por más de 3 segundos. Verifique que los **bordes de la pantalla brillen en Rojo** (Alarma de Seguridad).
*   [ ] **Detección de Llave**: Con el sistema en la pantalla de ventas (sin cobrar nada), abra el cajón con la llave física. El sistema debe detectar la intrusión, **disparar la alarma roja** y generar un registro en la base de datos automáticamente.

---

## 💳 2. COBRO INTELIGENTE Y AJUSTES (PASO 6)
*   [ ] **Enter Inteligente (Triple Enter)**: 
    1.  **ENTER**: Selecciona el método y salta al casillero de monto.
    2.  **ENTER**: Confirma el monto ingresado.
    3.  **ENTER**: Cierra la venta **SIN imprimir ticket** (igual que F2).
    Verifique que el flujo sea rítmico y sin errores.
*   [ ] **Modificadores F3/F4**: Antes de cobrar, presione **F3**. Ingrese un descuento. Verifique que el "Total a Pagar" disminuye visualmente. Repita con **F4** para un recargo.
*   [ ] **Finalización Silenciosa (F2)**: Elija "Efectivo", ingrese el monto y presione **F2**. Verifique que el cajón se abra pero **no salga papel**.

---

## 👮‍♂️ 3. INTERVENCIÓN DE SUPERVISOR (F11)
*   [ ] **Acceso Autorizado**: Presione F11, ingrese el PIN de Admin. Verifique que el cajón se abra y **NO suene la alarma** de inmediato (intervención autorizada).
*   [ ] **Burbuja Bombero**: Confirme que aparece la burbuja parpadeando en Rojo/Azul y que le permite navegar por todo el Admin.
*   [ ] **Sincronización Viva**: Cambie el precio de un producto en el Inventario. Regrese al terminal usando la burbuja. El producto que ya estaba cargado en el carrito **debe actualizar su precio automáticamente**.

---

## 🛒 4. TERMINAL INDUSTRIAL (PASO 5)
*   [ ] **Selección de Estación (F8)**: Alterne entre Cajero 1 y Auxiliar 2. Verifique que los tickets salgan por la impresora correcta asignada en la configuración.
*   [ ] **Balanza EAN-13**: Escanee un código de balanza (Ej: `2000005001257`). Verifique que el sistema desglose el importe exacto ($125.70) y asigne el peso automáticamente.
*   [ ] **Artículo Común**: Escriba `+100` y presione ENTER. Debe aparecer "ARTICULO COMUN" con precio de $100.00.

---

## 🏁 5. CIERRE Y AUDITORÍA (F12)
*   [ ] **Cierre Ciego**: Como cajero, realice un cierre. Ingrese un monto físico diferente al sistema. Verifique que el ticket de arqueo muestre la diferencia y que la app se **reinicie al login** inmediatamente.
*   [ ] **Reporte de Alertas**: Como admin, entre a F12 y verifique que la tarjeta **"Alertas Seguridad"** muestre el número exacto de aperturas con llave que realizó durante las pruebas anteriores.

---
*Si todos los puntos tienen check [x], el sistema está listo para producción.*
