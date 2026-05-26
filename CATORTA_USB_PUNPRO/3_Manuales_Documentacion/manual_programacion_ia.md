# 📘 MANUAL DE PROGRAMACIÓN CON IA: CajaFacil Pro

Este documento guía al desarrollador o administrador sobre cómo interactuar con el asistente de IA (Antigravity) para mantener, escalar y auditar el código del sistema.

---

## 🤖 1. FILOSOFÍA DE DESARROLLO AGÉNTICO
El sistema ha sido construido bajo una arquitectura de "Cero Lag" y "Blindaje de Hardware". Al solicitar cambios a la IA, use los siguientes principios:

1.  **Contexto Industrial**: Recuerde siempre a la IA que el sistema se usa en terminales de alto tránsito sin ratón.
2.  **Prioridad de Teclado**: Cualquier función nueva debe ser mapeada a una tecla `F` o atajo.
3.  **Seguridad Bidireccional**: Si se modifica la impresora o el cajón, se debe mantener el protocolo de polling `DLE EOT` para evitar descuadres.

---

## 🛠️ 2. CÓMO SOLICITAR CAMBIOS (PROMPTING)

### Para corregir errores (Debugging)
*   *Mal*: "No funciona el cobro."
*   *Bien*: "El módulo `paso6_cobro.py` muestra una alerta crítica al presionar F1. Revisa si el diccionario `resultado_venta` tiene todos los campos requeridos por `guardar_venta_completa` en `database.py`."

### Para añadir funciones (Feature Request)
*   *Ejemplo*: "Implementa un botón de Recargo Global en `paso6_cobro.py`. Usa el componente `DialogoMontoRápido`, asígnale la tecla **F4** y asegúrate de que el total final se actualice visualmente."

---

## 📂 3. ESTRUCTURA DE ARCHIVOS CRÍTICOS
Al programar, asegúrese de que la IA respete la ubicación de los archivos:
*   `src/cajero/`: Lógica de flujo de venta.
*   `src/admin/`: Paneles de supervisión.
*   `src/hardware/`: Controladores de bajo nivel (Printers/Scales).
*   `src/ui_components/`: Widgets reutilizables (Botones, diálogos, balizas).

---

## 🔒 4. MANTENIMIENTO DE LA BASE DE DATOS
Cualquier cambio en el esquema debe ser notificado. El sistema usa **SQLite en modo WAL** (Write-Ahead Logging) para permitir concurrencia. No modifique las transacciones de `guardar_venta_completa` sin asegurar que el `rollback` esté activo en caso de fallo.

---
*Guía de Desarrollo IA - PunPro Software Systems 2026*
