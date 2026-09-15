# Módulo: Panel Central (Columna 2) - Topología y Métricas

Este módulo gestiona la **Segunda Columna** del Nexus Control Center. Su propósito es renderizar visualmente el estado de la red (Computadoras conectadas) y las métricas macro de dinero en tiempo real.

## Arquitectura (MVC Componentizado)

- **
exus_panel_cen.py**:
  Orquestador del Panel Central. Se encarga de instanciar la grilla de Nodos (Cajas, Cartelerías, Cajeros) y las tarjetas de Métricas (Efectivo, Tarjetas, Ventas Remotas).

- **cyber_node_card.py**:
  Widget que representa gráficamente una Computadora en la red. Cambia de color dependiendo del estado (Online/Offline) y del tipo de nodo (Admin, Caja, Cartelería).

- **cyber_metric.py**:
  Widget que representa un bloque de métrica financiera (ej. "Total Efectivo Caja"). Posee animaciones sutiles y estilos de alto contraste.

## Características Clave
- **Renderizado Dinámico de Topología**: Recibe diccionarios de estado desde el 
exus_controller y dibuja o destruye CyberNodeCards para reflejar exactamente quién está conectado.
- **Inyección de KPIs Financieros**: Actualiza montos globales en tiempo real sin recargar toda la interfaz, comunicándose directamente con las CyberMetrics.
