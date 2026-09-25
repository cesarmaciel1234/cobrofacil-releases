# Propuesta de Mejora de Interfaz (Cliente y Cajero)

Analizando la pantalla actual de **Cobro (Transferencia / Mercado Pago)**, podemos aplicar mejoras de UX/UI centradas en dos pilares: **Legibilidad a distancia (para el cliente)** y **Velocidad de operación (para el cajero)**.

## 1. Organización Visual y Jerarquía (Layout)
* **Agrupar la información financiera:** El monto total ($100.00) está desconectado visualmente de los ajustes menores (Redondeo y Recargo). Deberían estar agrupados en un panel de "Resumen de Cuenta" o ticket virtual a la izquierda.
* **Destacar el Método de Pago:** "MÉTODO: TRANSFERENCIA" está relegado al rincón inferior izquierdo. Para el cajero es vital saber en qué contexto de pago está. Debería estar en el encabezado principal (ej. "COBRO - TRANSFERENCIA").

## 2. Rediseño del Panel de Acción (Derecha)
* **Código de Colores Semántico:** Actualmente hay muchos botones con colores vibrantes y distintos (Azul, Verde, Naranja, Celeste, Rojo, Gris). Esto genera fatiga visual.
  * **Acción Principal:** `ENTER` (o Confirmar) debe ser el botón más destacado.
  * **Teclado Numérico (Numpad):** Debe tener mayor contraste. Un fondo ligeramente oscuro con números claros, o botones blancos con sombras suaves y números en gris oscuro, para facilitar el tipeo rápido.
  * **Acciones Secundarias (F1-F12):** Deberían agruparse por contexto (ej. Impresión por un lado, Modificadores por otro) y usar una paleta de colores coherente y más neutra, reservando los acentos de color solo para lo importante.

## 3. Mejoras para el Cliente (Transparencia y Confianza)
* **Perfil del Cliente / Alias:** La caja blanca del "ALIAS" está bien, pero se puede mejorar poniéndole un ícono de perfil (Avatar) y diferenciando más el nombre de usuario (`cesar.maciel`) del nombre legal (`CESAR JAVIER MACIEL`).
* **Estado de Conexión:** El mensaje "ESCUCHANDO MERCADO PAGO EN TIEMPO REAL..." tiene un diseño de botón pero parece ser un indicador de estado. Debe lucir como un **Banner de Estado** (por ejemplo, con un fondo verde suave y un ícono de radar o spinner animado) para que tanto el cliente como el cajero entiendan que el sistema está esperando la transferencia.

## 4. Limpieza de Elementos Secundarios
* **Botón "Cajero silencioso":** Si es una opción de accesibilidad o notificación, ocupa mucho espacio central. Podría ser un interruptor (toggle) más discreto en la barra superior o inferior.
* **Inputs de Redondeo y Recargo:** Ocupan mucho espacio horizontal. Se podrían integrar directamente en el panel lateral derecho (bajo el Numpad) o en el resumen del monto.
* **"Cambiar (Esc)":** El botón para volver/cambiar método está oculto abajo. Debe ser más prominente o estar alineado a las acciones principales (como botón de retroceso superior).

---

### ¿Cómo procedemos?
Si te parecen bien estas directrices, puedo:
1. **Modificar el layout de `paso6_cobro.py`** para aplicar esta nueva jerarquía y paleta de colores.
2. Refactorizar los estilos (QSS) para mejorar el contraste de los botones y el teclado numérico respetando las reglas de los temas Globales (Día/Noche).
3. Asegurar que los componentes sigan modulares según `modularizacion.md`.

¿Querés que avance generando una previsualización de estos cambios o preferís ajustar algo de la propuesta?
