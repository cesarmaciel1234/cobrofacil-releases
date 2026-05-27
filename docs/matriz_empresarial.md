# 📊 MATRIZ OPERATIVA EMPRESARIAL: Cobro Fácil POS

Esta tabla detalla la arquitectura funcional del sistema, dividida por perfiles de responsabilidad y módulos técnicos.

| MÓDULO | FUNCIÓN PRINCIPAL | PERFIL CAJERO | PERFIL ADMINISTRADOR | TECNOLOGÍA / LÓGICA |
| :--- | :--- | :--- | :--- | :--- |
| **Login (Paso 3)** | Control de acceso y roles. | Selección de Estación 1/2 con PIN. | Acceso total a paneles de gestión. | Encriptación SHA-256 / Roles. |
| **Apertura (Paso 4)** | Registro de capital inicial. | Declara fondo fijo de cambio. | Supervisa apertura de turno. | Registro en `movimientos_caja`. |
| **Terminal (Paso 5)** | Venta y atención al cliente. | Escaneo, pesaje y carga de ítems. | Intervención (F11) para ajustes. | Multiprocesamiento / F-Keys. |
| **Cobro (Paso 6)** | Cierre de transacciones. | Cobro, vuelto y emisión de ticket. | Configuración de medios de pago. | Bloqueo por hardware ESC/POS. |
| **Cierre Z (Paso 7)** | Rendición de cuentas. | Arqueo Ciego (Sin ver sistema). | Reporte Global y Auditoría. | Algoritmo de Conciliación. |
| **Historial (Paso 8)** | Auditoría de ventas. | Consulta diaria y reimpresiones. | Anulaciones y Auditoría Histórica. | Filtrado en memoria ultra-veloz. |
| **Inventario** | Control de existencias. | *Solo lectura de precios.* | Alta, Baja y Cambio de Precios. | Integridad Referencial SQLite. |
| **Ofertas** | Motor de promociones. | Aplicación automática por cant. | Creación de reglas de descuento. | Lógica de Descuento en Cascada. |
| **Seguridad** | Vigilancia de hardware. | Alerta por cajón abierto. | Reporte de aperturas con llave. | Polling ESC/POS (Bit 3). |
| **AI Boss** | Inteligencia de Negocio. | *Sin acceso.* | Análisis predictivo de ventas. | Algoritmos de Tendencia. |
| **Hardware** | Configuración periféricos. | Uso de impresora asignada. | Mapeo de puertos y balanzas. | Drivers RAW / Bidireccional. |

---

## 🛠️ DESGLOSE TÉCNICO DE FUNCIONAMIENTO

### 💎 Modo Cajero (Operación de Alto Tráfico)
*   **Velocidad**: Optimizado para 0% uso de mouse. Todo se procesa vía `F1-F12`.
*   **Blindaje**: El cajero no conoce los totales del sistema (Arqueo Ciego). Esto evita el "robo hormiga".
*   **Estabilidad**: El modo Kiosko impide que el cajero minimice la app o acceda a Windows.

### 👑 Modo Administrador (Gestión y Supervisión)
*   **Intervención en Vivo (F11)**: Permite saltar del terminal a la gestión sin cancelar la venta del cliente.
*   **Auditoría de Llave**: El administrador recibe un reporte de cada vez que el cajón se abrió manualmente sin una venta.
*   **Sincronización**: Al usar la "Burbuja Bombero", el administrador actualiza los precios en el Admin y estos se aplican al terminal instantáneamente al volver.

---
*Cobro Fácil POS - Manual Técnico-Empresarial de Referencia*
