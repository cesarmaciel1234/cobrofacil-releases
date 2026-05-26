# 📔 Diario de Aprendizaje: Proyecto PunPro

¡Hola! Aquí anotamos los pasos del programa para aprender cómo funciona todo. PunPro tiene **dos caminos** dependiendo de quién entre a trabajar.

---

## 👨‍💼 CAMINO 1: EL ADMINISTRADOR (El Jefe)
El jefe es quien controla el negocio. No vende, sino que organiza. Sus pasos son:

1.  **🔑 Paso 1 (Licencia)**: Entra al programa con su llave de permiso.
2.  **👤 Paso 2 (Perfil)**: Elige el botón "ADMINISTRADOR".
3.  **📝 Paso 3 (Login)**: Pone su nombre de jefe.
4.  **📦 Paso Especial (Inventario)**: Entra a la oficina de **Gestión de Inventario**. (Archivo: `src/admin1_inventario.py`).
5.  **💹 Paso Especial (Masivo)**: Cambia precios de todo el negocio de una vez. (Archivo: `src/admin2_masivo.py`).

---

## 🛒 CAMINO 2: EL CAJERO (El que vende)
El cajero es el que atiende a los clientes rápido. Sus pasos son:

1.  **🔑 Paso 1 (Licencia)**: Igual que el jefe, necesita permiso.
2.  **👤 Paso 2 (Perfil)**: Elige el botón "CAJERO".
3.  **📝 Paso 3 (Login)**: Pone su nombre de vendedor.
4.  **💰 Paso 4 (Apertura)**: Cuenta el dinero inicial para abrir la caja.
5.  **🛒 Paso 5 (Terminal)**: Escanea los productos en la pantalla negra (usando el sistema *Carlis* o la tabla industrial).
6.  **💵 Paso 6 (Cobro)**: Cobra al cliente en la ventana clonada y entrega el vuelto.

---

## 💡 Notas de Programación: Conceptos Clave
- **Roles (Perfiles)**: Es como en un equipo de fútbol; el arquero tiene guantes (Admin) y el delantero tiene botines (Cajero). Cada uno ve herramientas diferentes.
- **Base de Datos (SQLite)**: Es el archivador gigante donde se guardan los precios. Si el jefe cambia un precio en su pantalla, el cajero lo verá actualizado al instante en la suya.
- **Navegación Circular**: El cajero usa el teclado (`Shift`, `F1`, `Enter`) para ir volando sin tocar el mouse.

---
*Este diario nos ayuda a no perdernos en el código y a entender el flujo del negocio.*
