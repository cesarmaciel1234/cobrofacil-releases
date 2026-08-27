# Plan de Mejora - Cartelería HTML

## 📋 Estado Actual
- ✅ Layout full-screen expandido (el carrusel de ofertas ahora abarca de manera continua las 4 pantallas).
- ✅ Carrusel unificado estilo marketplace con publicidad.
- ✅ Flash strip con contador regresivo.
- ✅ Header flotante con estado y reloj.
- ✅ Integración con motores globales (publicidad, clima, IA).
- ✅ Sistema de temas autónomo.
- ❌ **El Chef Lobo fue despedido** (Personaje e IA asociada retirados completamente de la cartelería).

## 🎯 Plan de Mejoras Prioritarias

### 1. Optimización de Performance (Vista Ultra-Wide) 🚀
**Objetivo:** Reducir tiempo de carga y garantizar máxima fluidez a lo largo de las 4 pantallas.

**Acciones:**
- Implementar lazy loading sincronizado para todas las imágenes del carrusel gigante.
- Usar CSS containment para el track del carrusel (`contain: layout style paint;`).
- Optimizar animaciones de desplazamiento con `will-change: transform` y `transform: translateZ(0)`.
- Carga diferida de componentes publicitarios no críticos.
- Limpiar y remover código muerto relacionado al Chef Lobo en CSS y JS (`columna4_chef.css`, `lobo_chef.js`, etc.).

**Beneficios:**
- 30-40% de reducción en el tiempo de carga inicial.
- Carrusel ultra fluido y sin saltos al cruzar entre monitores.
- Liberación significativa de RAM y CPU al remover al personaje interactivo.

### 2. Sincronización y Transiciones Suaves ✨
**Objetivo:** Experiencia visual profesional continua sin cortes bruscos.

**Acciones:**
- Transiciones suaves y continuas del carrusel a lo largo de la matriz de TVs.
- Fade-in/out sincronizado para cambios de tema globales.
- Compensación de biseles (Bezel Correction) para que las tarjetas de productos no se deformen en las uniones de las TVs.
- Skeleton loading dinámico mientras cargan los datos de las ofertas.

**Beneficios:**
- Sensación de una única pantalla gigante inmersiva.
- Evita productos cortados a la mitad por los marcos de las pantallas.
- Feedback visual mejorado para los clientes en sala.

### 3. Responsive Design Avanzado (Multi-Monitor) 📺
**Objetivo:** Perfecto ajuste para cualquier matriz de pantallas combinadas.

**Acciones:**
- Configuración de resolución panorámica combinada (Ej: 7680x1080px para 4 monitores Full HD).
- Adaptive sizing para asegurar que las tarjetas de productos mantengan una proporción legible a la distancia.
- Zonas seguras (Safe Zones) dinámicas basadas en los bordes del hardware.
- Escala de tipografía global basada en la distancia promedio del espectador.

**Beneficios:**
- Continuidad perfecta e impacto visual maximizado.
- Ajuste universal sin importar si son pantallas de 32", 55" o 85".

### 4. Sistema de Rotación y Publicidad Inteligente ("Takeover") 🔄📢
**Objetivo:** Publicidad espectacular que aproveche todo el espacio.

**Acciones:**
- Formato **Takeover**: Permitir que un solo anuncio o promoción tome las 4 pantallas temporalmente.
- Rotación del carrusel basada en hora del día y stock disponible (para no promocionar productos agotados).
- Integración de IA para recomendaciones globales (cross-selling).
- Segmentación publicitaria por categorías y programación horaria.

**Beneficios:**
- Efecto WOW que capta 100% la atención del cliente.
- Mayor rentabilidad por espacios publicitarios en tienda.
- Contenido sumamente relevante y actualizado en tiempo real.

### 5. Monitoreo, Analytics y Accesibilidad 📊♿
**Objetivo:** Medir rendimiento técnico e impacto comercial.

**Acciones:**
- Performance tracking de FPS específico para arreglos multi-pantalla.
- Métricas de productos más visualizados (Tiempo en pantalla).
- A/B testing de tiempos de desplazamiento del carrusel.
- Soporte para alto contraste (WCAG) y temas nocturnos o para tiendas con alta iluminación.

**Beneficios:**
- Decisiones respaldadas por datos reales.
- Detección inmediata si un monitor sufre caídas de cuadros.
- Mejor legibilidad para todo tipo de clientes.

## 📅 Roadmap de Implementación

### Fase 1 (Inmediata - 1 semana)
1. **Refactorización de limpieza**: Eliminar los archivos CSS, JS y módulos antiguos del Chef Lobo (limpiar `columna4` y `lobo.db`).
2. Implementar la estructura CSS ultra-wide (`width: 400vw` o contenedor global en lugar de 4 columnas separadas).
3. Ajuste inicial de Bezel Correction (Compensación de bordes).

### Fase 2 (Corto plazo - 2 semanas)
4. Sincronización del lazy loading en el carrusel de ofertas unificado.
5. Monitoreo de FPS para evaluar el impacto en la tarjeta gráfica del servidor TPV.
6. Habilitar la primera versión del formato publicitario "Takeover".

### Fase 3 (Mediano/Largo plazo - 1 a 2 meses)
7. Integración avanzada de la IA (ahora orientada a la sugerencia general de productos, sin avatar).
8. A/B testing de velocidad del carrusel para maximizar el tiempo de retención visual del cliente.
9. Despliegue del sistema de métricas de impacto comercial.

## 🚀 Próximos Pasos Técnicos

1. Entrar a `src/carteleria/lanzador_tv/la_cara_web/` y desvincular `columna4_chef.css` y `columna4.js`.
2. Actualizar `app.js` e `index.html` para remover la estructura de 4 columnas independientes y usar un layout Flex/Grid unificado para el carrusel principal.
3. Probar en los monitores físicos la nueva velocidad de desplazamiento.