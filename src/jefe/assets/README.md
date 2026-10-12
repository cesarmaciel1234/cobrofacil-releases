# Íconos de Módulos Jefe

Este directorio contiene los íconos PNG para los módulos del perfil Jefe.

## Configuración Actual

Actualmente los módulos usan emojis Unicode que funcionan bien en la mayoría de sistemas:
- Reportes: 📊
- Nexus Pro: 🌌
- Corte Caja: 💰
- Red LAN: 🌐
- Proveedores: 🚚
- Promedios: ⚖️
- IA Proactiva: 🧠
- Personal: 👥

## Cómo usar PNGs (Opcional)

Si prefieres usar imágenes PNG en lugar de emojis:

1. Coloca tus PNGs en este directorio (`src/jefe/assets/`)
2. Nombra los archivos según el ID del módulo:
   - `reportes.png`
   - `nexus_pro.png`
   - `corte_caja.png`
   - `red_lan.png`
   - `proveedores.png`
   - `promedios.png`
   - `ia_proactiva.png`
   - `personal.png`

3. En `jefe0_dashboard.py`, cambia la línea de JEFE_MODULES:
   ```python
   # De emoji:
   ("reportes", "Reportes\ny Ventas", "📊", ...)

   # A PNG:
   ("reportes", "Reportes\ny Ventas", "reportes.png", ...)
   ```

4. El componente `JefeCard` buscará automáticamente el PNG en:
   - `src/jefe/assets/{nombre}`
   - `src/assets/{nombre}`

## Resolución recomendada

- PNGs: 64x64 o 128x128 píxeles
- Formato: PNG con transparencia
- El componente escala automáticamente a 40x40

## Fallback automático

Si el PNG no existe o falla la carga, el componente usa automáticamente el emoji de fallback (📊) sin romper la UI.
