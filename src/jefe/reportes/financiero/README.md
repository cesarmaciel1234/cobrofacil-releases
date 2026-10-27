# Reporte Financiero

Submódulo de Reportes que genera las estadísticas y KPIs de ventas (resumen por día, mes, medios de pago, ganancias, etc.).

## Función
`consulta.py`: Expone las funciones de recolección de datos (como `kpis_rango` y `payload_reporte_global`) usando los filtros de periodo.

## Cómo funciona
1. La vista (`vista_financiero.py`) llama a `cargar_datos(periodo)`.
2. Las consultas a la base de datos se hacen a través de la función `_db()`, que garantiza el **aislamiento de motores**.
3. Si la red está activa, `_db()` devuelve una conexión a MariaDB (`db_manager`).
4. Si la red está caída (microcorte) y el panel detecta que está offline, `_db()` devuelve `espejo.fuente()` (el Lector del archivo SQLite de solo lectura `espejo_tienda.db`).
5. Se renderizan las gráficas sin interrumpirse, usando siempre los datos reales de la tienda (online o en copia espejo), nunca de la base de cobro offline.

## Rótulos

`rotulos.py` guarda los textos que se ven: días (`Mié`, `Sáb`), el título «Ventas por día» y la columna `Día`. Están escritos con escapes (`\u00e9`) para que un guardado con el código de página equivocado no los vuelva a dejar como `MiÃ©`.

`titulo_serie(periodo)` elige el título. `nombre_dia(fecha)` arma `Mié 07`. `es_anio(periodo)` reconoce «Año» de verdad; el texto roto `AÃ±o` no matchea el botón y el año se dibujaba como si fuera un mes.

La torta no escribe nombres encima de las porciones. El nombre va en la lista, con un punto de color. El centro de la torta solo muestra el total.

## Comparación

`periodo_previo.rango_completo_anterior` trae el periodo anterior entero. En la semana, es de lunes a domingo aunque la semana en curso vaya por el martes. `clave_anterior` apoya cada día que todavía no llegó en el mismo día de la semana pasada: eso es la proyección.

Con «Comparar» prendido, las tarjetas de arriba se parten en dos. El título sale de `nombres_comparacion` (Semana en curso / Semana pasada, Mes en curso / Mes pasado, Hoy / Ayer). La tabla de días cierra con una fila Total: la suma en curso y la suma pasada.

## A la altura de una cadena local

Con «Comparar» prendido, el reporte firma esto:

- `kpis_rango` es el número de las tarjetas. `serie_diaria` es el mismo filtro, partido por día. El pie suma esa serie.
- `rango_completo_anterior` trae la semana, el mes o el año anterior enteros. Los departamentos y los pagos usan esa misma ventana.
- `mismo_tramo` corta el periodo anterior a la hora de ahora. La tarjeta lo muestra como «Mismo tramo». La semana pasada entera sigue en la otra tarjeta.
- `proyectar` suma lo ya vendido más los días que faltan, tomados del periodo pasado. Si uno de esos días es feriado, suma cero. La fila se llama Proyección.
- `feriados.py` marca el día. No lo esconde. Son los feriados nacionales de Argentina, fijos y los que se trasladan al lunes, más Jueves y Viernes Santo y el carnaval.
- `rango_anio_pasado` es la misma semana (364 días, para conservar el lunes), el mismo mes o el mismo día del año anterior. En la tarjeta dice «Año pasado».
- `cobertura` dice qué porcentaje de la venta tiene costo cargado. Sin costo, la ganancia sigue diciendo «Sin costo».
- La plata de esta tabla y de las tarjetas sale de `fmt_plata`.

Lo que sigue afuera: varias sucursales en la misma pantalla, y el feriado puente que un decreto mueve y no está en la lista.

## Qué no cambiar
- **No reemplazar `_db().execute_...` por llamadas directas a `db_manager.execute_...` en la vista financiera.** Llamar a `db_manager` directamente en la vista provoca que, ante una falla de red, el reporte consulte `punpro.db` (la base de caja offline), arrojando gráficos en **$0.00**. La lectura debe pasar siempre por el enrutador `_db()` para mantener separado el motor de la tienda del motor de cobro local.
