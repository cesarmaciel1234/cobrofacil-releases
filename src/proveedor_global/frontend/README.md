# Frontend - Vista Proveedor

Esta subcarpeta contiene únicamente la capa de presentación de la gestión de proveedores.

- **Qué hace:** Provee la clase VistaProveedor, un widget de PyQt6 que renderiza el formulario de carga de romaneos y el historial de compras.
- **Cómo funciona:** Reacciona a las acciones del usuario recolectando los datos del formulario y delegando toda la ejecución a los métodos estáticos del motor en el backend. Presenta los datos devueltos en tablas.
- **Qué devuelve cuando falla:** Atrapa las excepciones del motor mediante cuadros de diálogo (QMessageBox.warning o critical) informando al usuario.
- **Qué no debe cambiar una mejora futura:** No se debe incluir código SQL ni lógicas de negocio, cálculos de stock o gestión de SQLite dentro de esta interfaz. Toda operación sobre datos viaja por motor_proveedor.py.
