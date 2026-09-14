# Cartelería — reglas del servidor

Mismo motor que **jefe**. El puesto se guarda en `config.json` como en el resto.

## TV como MAESTRA

Sirve para apagar la PC de caja: al iniciar el lanzador (o `--server` / Win: ON) la TV despierta MariaDB. Las cajas esclavas ya tienen esa IP.

## TV como ESCLAVA

Al encender **no** levanta servidor. Lee catálogo, publicidad y reporte de la maestra (`db_host`). No usa el `punpro.db` de la TV como tienda. Ver `src/base_de_datos/reglas.md`. Si un día la convierten en maestra, desde ese boot sí despierta MariaDB.

## Arranque del perfil

Si no hay `--server` y no es esclava → `init_lan_server()`.
Si el lanzador ya dejó `--server` ONLINE, cartelería no duplica mysqld.

## Reporte global

La TV consulta los mismos KPI que el jefe: `GET /api/carteleria/reporte`
(hoy, semana, mes, días trabajados, aviso de costo). No inventa números.
