# Módulo: Panel Izquierdo (Columna 1) - Terminal SYS.OP

Este módulo gestiona la **Primera Columna** del Nexus Control Center. Su propósito es actuar como una **Consola de Sistema (Terminal SYS.OP)** que muestra en crudo el flujo de datos y mensajes de estado global (Startups, Errores Críticos, Heartbeats interceptados de bajo nivel).

## Arquitectura

- **
exus_panel_izq.py**:
  Contiene la clase NexusPanelIzq, que administra el QTextEdit principal que sirve de consola. Expone métodos públicos como ppend_log para que el controlador inyecte texto con formato HTML (verde para OK, rojo para errores, azul para sistema).

## Características Clave
- **Scroll Inteligente**: Autoscroll hacia el final cada vez que entra un nuevo log de sistema.
- **Modo Hacker/Cyber**: Por diseño, se mantiene con un fondo oscuro y fuentes monoespaciadas para dar el aspecto de terminal de infraestructura, contrastando con las columnas de analítica.
