# Migración PyQt5 → PyQt6 — Cobro Fácil POS

## Estado actual

| Componente | Estado |
|------------|--------|
| Producción | **PyQt5** (`requirements.txt`) |
| Capa compat | `src/utils/qt_compat.py` |
| Bootstrap | `main.py`, `qt_dpi.py`, `main_window.py` preparados |
| Animaciones float | `VariantFloatAnimation` (reemplaza `QVariantAnimation`) |
| Auditoría | `python tools/pyqt6_audit.py` |

## Cómo probar PyQt6 (rama local, sin romper prod)

```powershell
pip install -r requirements-pyqt6.txt
$env:TPV_QT = "6"
python tools/pyqt6_audit.py --strict
python main.py
```

Volver a PyQt5: quitar `TPV_QT` o `$env:TPV_QT = "5"`.

## API de compatibilidad

```python
from src.utils.qt_compat import (
    qt_exec,                    # reemplaza .exec_()
    screen_geometry_at,         # reemplaza QApplication.desktop()
    screen_count,
    VariantFloatAnimation,      # reemplaza QVariantAnimation
    configure_qt_application_attributes,
    set_share_opengl_contexts,
    binding_info,
    IS_QT6,
)
```

## Orden de migración recomendado

### Fase 0 — Hecho
- [x] `qt_compat.py`
- [x] `main.py` → `qt_exec`, `set_share_opengl_contexts`
- [x] `main_window.py` → `screen_geometry_at`
- [x] `terminal_caja_mixin.py` / `paso5_terminal.py` → `VariantFloatAnimation`
- [x] Auditoría y tests

### Fase 1 — Hecho
- [x] `qt_compat.py` + `qt_exec()` en **todo el proyecto** (~120 llamadas)
- [x] Rama `feature/pyqt6`
- [x] Smoke test: `python tools/smoke_pyqt6.py` (requiere `requirements-pyqt6.txt`)

### Fase 2 — Hecho (rama `feature/pyqt6`)
- [x] Imports `PyQt5` → `PyQt6` en ~109 archivos
- [x] `requirements.txt` → PyQt6 + PyQt6-WebEngine
- [x] `qt_printer.py` — QPrinter, márgenes, `print_document`
- [x] `QAction` → `QtGui` (admin10_mp)
- [x] `compileall` OK + smoke PyQt6 OK

### Fase 3 — Hecho
- [x] `invoke_method()` en `qt_compat` — `github_updater`, `admin13_hardware`
- [x] WebEngine: `connect_webengine_console`, `webengine_page_transparent`
- [x] `chat_bot.py`, `chat_bot_animado.py` adaptados a Qt6
- [x] `tools/smoke_webengine.py`

### Fase 4 — Cajero + empaquetado (siguiente)
| API PyQt5 | PyQt6 |
|-----------|-------|
| `QApplication.desktop()` | `app.screens()[i].availableGeometry()` |
| `QVariantAnimation` | `VariantFloatAnimation` |
| `AA_EnableHighDpiScaling` | `setHighDpiScaleFactorRoundingPolicy` |
| `QPrinter.HighResolution` | `QPrinter.PrinterMode.HighResolution` |
| `QDesktopServices` | `QtGui.QDesktopServices` |
| `QMetaObject.invokeMethod` + `Q_ARG` | Revisar tipos / usar señales |

### Fase 4 — QtWebEngine (crítico)
Archivos: `chat_bot.py`, `chat_bot_animado.py`, `Instalador_Web.py`

- Validar `--disable-gpu` y `AA_ShareOpenGLContexts` en Qt6.
- PyInstaller: `PyQt6.QtWebEngineWidgets` + collect hooks.
- El chatbot corre como subproceso `pythonw` → actualizar instalador.

### Fase 5 — Cajero (último, regresión visual)
`paso5` → `paso8`, `styles.qss`, teclas F, hardware.

### Fase 6 — Empaquetado
- `requirements.txt` → PyQt6
- `.github/workflows/release.yml`
- `CobroFacil_POS.spec`, `Compilar_Todo.bat`, specs del instalador

## Reglas del proyecto

- **Cajero** (`src/cajero/`): cambios mínimos; probar terminal completo tras cada fase.
- **Temas**: cajero oscuro (`styles.qss`); admin/jefe claro (`styles_light.qss`) — QSS compatible con Qt6.
- **DPI**: `src/utils/qt_dpi.py` — revisar atributos obsoletos en Qt6.

## Métricas (ejecutar auditoría)

```powershell
python tools/pyqt6_audit.py
```

Blockers restantes típicos tras Fase 0: `exec_()` masivo, imports `PyQt5`, WebEngine.
