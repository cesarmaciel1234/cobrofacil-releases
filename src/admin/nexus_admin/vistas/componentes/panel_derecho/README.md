# Módulo: Panel Derecho (Columna 3) - Monitor de Auditoría y Flujo en Vivo

Este módulo maneja de manera independiente la **Tercera Columna** del Nexus Control Center. Su propósito es actuar como un **Sub-Monitor Dedicado en Vivo** que permite al usuario filtrar la enorme cantidad de ruido generado en la red y enfocarse solo en flujos específicos (Cobros, Cajones, Alertas, o Acciones del Sistema).

## Arquitectura (MVC Componentizado)

Este componente ha sido modularizado y "encarpetado" bajo el estándar piramidal para sistemas corporativos:

- **
exus_panel_der.py (Controlador/Vista del Componente)**
  Es el núcleo del panel derecho. Gestiona la lógica del filtro en tiempo real, interactúa con CerebroNexus para la paginación de la base de datos (historial) e inyecta dinámicamente nuevas tarjetas cuando el 
exus_controller.py intercepta eventos UDP relevantes.

- **cyber_feed_item.py (Widget/Modelo de Vista)**
  Representa gráficamente una tarjeta (Card) de evento individual. Ha sido separada de la lógica del panel principal para permitir un pintado independiente y reutilizable. Es un QFrame inteligente que se adapta al Light Mode o Dark Mode heredado del ecosistema de Cobro Fácil, coloreando su borde izquierdo según la naturaleza crítica del evento (Rojo=Seguridad, Verde=Cobros, etc.).

## Características Clave

1. **Re-pintado Dinámico (Live-Injection):**
   Las tarjetas se inyectan mediante self.feed_layout.insertWidget(0, item) empujando el feed histórico hacia abajo sin parpadear (Flicker-Free), en lugar de recargar la base de datos de 0.
   
2. **Motor de Theming Acoplado:**
   Implementa update_theme(self, theme) para mutar los colores de su propio sub-entorno de acuerdo a la capa de diseño global (White / Dark mode).

3. **Restricciones de Hardware:**
   La UI ha sido asegurada con setMinimumWidth explícitos dentro de 
exus_main_view.py para garantizar que la Columna 3 no colapse bajo layouts asimétricos o monitores estrechos.

> **Reglas de Modificación:** Todo componente visual nuevo para la Columna 3 debe crearse como un archivo .py independiente dentro de este directorio e instanciarse dentro de 
exus_panel_der.py.
