# Plano — contabilidad

## Frente

Pantalla del jefe. Barra con mes, año y backup. A la izquierda, la lista de vistas. El fondo sigue el día o la noche global.

## Fondo

`JefeContabilidad._load_db_and_build` llama `get_jefe_db_path()` y abre `Database`. El backup de `VistaReportesMixin._do_backup` copia `self._db.db_name`.

`shared_globals.paleta_global` arma los colores desde `theme_manager` según `config` `theme`. `JefeContabilidad._repintar_por_tema` rearma la pantalla si el tema cambió mientras estaba cerrada.

## Qué no cambiar

No volver a `theme_pro.THEME_PRO`. No fijar la ruta de la base al importar el módulo.
