# Cerebro operativo

## Frente

No abre una pantalla ni envía mensajes. Entrega una lista única de acciones para que el panel del Jefe, Proveedores u otra interfaz pueda mostrar qué preparar primero. Cada acción dice de qué motor salió, cuánto propone, por qué y si todavía requiere revisión humana.

## Fondo

`eventos/` recibe hechos con un id único y los deja auditables en la base. `politicas/` guarda reglas versionadas. `planificacion/` transforma el panorama en un plan. `ejecucion/` guarda el borrador y permite avanzar por estados controlados. `observabilidad/` prepara las métricas para comparar una decisión con su resultado.

`motor/orquestador.py` consulta la compra predictiva y el resumen de abastecimiento ya existentes. `evaluar()` normaliza las propuestas y, cuando ambas hablan de la misma fórmula y unidad, conserva la cantidad mayor: nunca suma dos sugerencias. `preparar_plan()` guarda ese resultado como borrador y anota el evento correspondiente.

El cerebro no escribe inventario, precios, fórmulas, proveedores ni compras; tampoco envía WhatsApp. La compra predictiva puede seguir anotando su foto diaria de stock como hasta hoy. La base de datos es el corazón: los periféricos podrán registrar hechos por `eventos.registrar`, y las interfaces leerán planes consolidados, sin depender de la memoria de otro perfil.

## Qué no romper

Las reglas de bulto de Pollo, Carne, Cerdo, Congelado y Huevo siguen siendo dueñas de sus cantidades. Este módulo las coordina, no las recalcula. Un fallo en una fuente deja el resto de las acciones disponible. Los únicos estados válidos de un plan son `BORRADOR`, `APROBADO`, `DESPACHADO`, `RECIBIDO` y `CANCELADO`; no se saltean.
