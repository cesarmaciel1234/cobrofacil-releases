# Jefe — por dónde empezar

Esta carpeta es base. No lleva `plano.md`. Cada rama tiene el suyo.

No tocar `src/cajero/` ni el tema oscuro del terminal.

## Tema

Día y noche son globales. El botón del panel llama `aplicar_tema` con `estilo_dia.qss` o `estilo_noche.qss`. La clave es `config` `theme`: `light` o `dark`. Los colores vivos están en `src/utils/theme_manager.py`.

`theme_pro.py` está retirado. No tiene paleta. No lo vuelvas a llenar de hex.

La contabilidad pide colores a `contabilidad/shared_globals.py`, `PAL`. Esa paleta lee el tema global. Al volver a entrar en contabilidad después de cambiar día/noche, `JefeContabilidad._repintar_por_tema` arma de nuevo la barra y las vistas.

## Carpetas

| Carpeta | Qué es | Empezá por |
|---|---|---|
| `reportes/` | Ventas, auditoría, historial | `reportes/reglas.md` |
| `contabilidad/` | ERP del dueño, base aparte | `contabilidad/plano.md` |
| `ia/` | Cerebro Jefe (frases, no inventa números) | `jefe_ia_proactiva.py` |
| `vitrina/` | Publicidad izquierda del home (4 plazas). El nombre es `vitrina`, no `vitina` | `vitrina/reglas.md` |
| `promedios/` | Costos de carne, cerdo y pollo | `promedios/plano.md` |
| `nodo_portable/` | Copia USB / OneDrive | `nodo_portable/plano.md` |
| `componentes_visuales/` | Tarjetas del home | `componentes_visuales/README.md` |
| `servidor/` | Nota del puesto maestra/esclava | `servidor/reglas_servidor.md` |

## Números

Un solo dueño: `reportes/financiero/consulta.py` (`payload_reporte_global`).  
La TV y las esclavas **leen**. No recalculan.

## Red

Cualquier perfil en PC esclava lee la maestra. Ver `src/base_de_datos/reglas.md`.

## Qué no cambiar

No crear `plano.md` en `src/jefe`.

No pasar el espejo del nodo por `db_manager`. La copia de la tienda de esta PC (`nodo_portable/espejo`) y el pendrive se abren con `sqlite3`; la tienda se lee con una conexión pymysql propia. Sin maestra, los `_db()` de vitrina, financiero y auditoría devuelven `espejo.fuente()`. El plano de `nodo_portable` fija las vías.

La copia y el pendrive llevan toda la tienda (usuarios y configuración incluidos) y sirven para restaurarla con `src/base_de_datos/restaurar`. El jefe no restaura desde su panel: se hace en Mantenimiento → Respaldo. Para leer el pendrive hace falta el sistema instalado; la tienda trabaja con MariaDB.

En promedios, un `except` desnudo deja el número en `0` si la celda no es un número. Una fila vacía no se exporta. No los cambies por un log que escriba otro precio.

`pyttsx3` es opcional. Si no está, `HAS_TTS` queda en falso y `VozWorker` no habla. La pantalla del jefe sigue.

`WorkerExportAudit` escribe el Excel en un hilo y avisa con `finished`. No tiene barra de progreso ni cancelación.

`get_jefe_db_path()` se llama al abrir contabilidad, no solo al importar el módulo. El backup copia `self._db.db_name`, el archivo que está abierto.
