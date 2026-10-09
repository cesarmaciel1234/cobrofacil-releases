# Motor de Condiciones

## ¿Qué hace?
El Motor de Condiciones es una arquitectura empresarial que centraliza la generación de textos, condiciones legales, mensajes comerciales y de auditoría para todos los documentos impresos por el sistema (tickets de venta, abonos, cortes de caja, etc.).

## ¿Qué función cumple?
Aísla la lógica de negocio de los mensajes extraídos o generados dinámicamente de la capa de impresión o interfaz de usuario. Al mantener los mensajes en un solo lugar (orquestados por `MotorCondiciones`), se garantiza la consistencia global en toda la aplicación (Cajero, Admin, Jefe).

## ¿Cómo funciona?
Utiliza un diseño de "Fachada Orquestadora" mediante la clase `MotorCondiciones`. Ésta expone el método estático `obtener_condiciones(contexto, subcontexto, **kwargs)`. Según el `contexto` ('credito', 'venta', 'cierre'), la solicitud se delega a uno de los submotores especializados ubicados en sus respectivas carpetas, pasando los argumentos necesarios (como saldo_anterior, monto_actual, etc.) para que devuelvan el bloque de texto ya formateado.
