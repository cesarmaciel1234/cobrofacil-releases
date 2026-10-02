# Backend - Motor Proveedor

Esta subcarpeta contiene únicamente la lógica de negocio y las reglas de acceso a la base de datos para la gestión de proveedores.

- **Qué hace:** Provee la clase MotorProveedor, que actúa como el cerebro agnóstico de UI para el módulo.
- **Qué función:** 
  - save_proveedor: Inserta el romaneo, el detalle y la deuda en MariaDB.
  - pagar_proveedor: Cambia el status de una deuda en gastos a 'Pagado'.
  - load_proveedores y get_proveedores_unicos: Consultan la base de datos para armar el historial y los autocompletados.
- **Cómo funciona:** Interroga a 	ienda_disponible() para saber si la tienda MariaDB está en línea. Si lo está, abre una conexión, ejecuta las sentencias SQL mediante execute_query y execute_non_query, commitea la transacción y devuelve los resultados a la vista.
- **Qué devuelve cuando falla:** Lanza RuntimeError con el motivo explícito para que el frontend lo capture.
- **Qué no debe cambiar una mejora futura:** No se debe volver a aislar la lectura o escritura según el perfil. Las compras a proveedores son gastos globales del negocio y deben registrarse siempre en la tienda para que cualquier perfil (Jefe, Admin, Cartelería) que acceda al módulo vea la misma información centralizada.
