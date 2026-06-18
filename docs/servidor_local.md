# 🖥️ Guía de Configuración: Servidor Local (Red de Cajas)

El sistema **PunPro POS Elite 2026** incluye una base de datos principal (MariaDB/Motor de alta presión) que permite conectar hasta **20 computadoras (Cajas)** simultáneamente sin caída de rendimiento. 

Todas las cajas leerán y guardarán ventas al mismo tiempo en el mismo archivo `punpro.db` sin bloquearse.

---

## 1. Configurar la PC Principal (El "Servidor")

La PC Principal será la dueña de la base de datos real. Te recomendamos elegir la computadora más rápida de la red (Ej: Caja 1 o PC de Administración).

1. Abre tu carpeta donde instalaste el programa (ej: `D:\PunPro_Elite_2026`).
2. Asegúrate de que el programa se haya abierto al menos una vez para que se cree el archivo `punpro.db` adentro de esa carpeta.
3. Haz clic derecho sobre toda la carpeta `PunPro_Elite_2026` y elige **Propiedades**.
4. Ve a la pestaña **Compartir** -> **Uso compartido avanzado...**
5. Marca la casilla **"Compartir esta carpeta"**.
6. Haz clic en **Permisos** y asegúrate de marcar la casilla **"Control Total"** (o Lectura/Escritura) para el grupo *Todos* (o los usuarios de tu red). Acepta todo.

---

## 2. Configurar las Cajas Esclavas (Clientes)

Ahora ve a la Caja 2, Caja 3, etc. (Las que se van a conectar a la principal).

### A. Mapear la Unidad de Red
1. Abre el **Explorador de Archivos** de Windows y ve a **"Este equipo"** o **"Red"**.
2. Arriba en la ventana, busca el botón que dice **"Conectar a unidad de red"**.
3. En **Unidad**, elige una letra libre (por ejemplo, `Z:`).
4. En **Carpeta**, escribe la ruta compartida o dale a "Examinar" para buscar la carpeta de la PC Principal. (Ejemplo: `\\CAJA1-PC\PunPro_Elite_2026`).
5. Marca "Conectar de nuevo al iniciar sesión" y dale a Finalizar.
6. *¡Listo! Ahora en tu Caja 2 tienes un "Disco Z:" que en realidad es la carpeta de la Caja 1.*

### B. Indicarle al Programa Dónde Leer
1. En la Caja 2, abre la carpeta local donde tengas instalado el ejecutable (o simplemente corre el programa desde el Disco Z:).
2. Si prefieres tener el programa local pero apuntando a la base de datos de red, busca el archivo `config.json` que está en la carpeta de instalación de la Caja 2.
3. Ábrelo con el Bloc de notas.
4. Agrega la línea de `"db_path"` indicando la ruta del disco mapeado que llega directo a `punpro.db`. Debería verse así:

```json
{
    "business_name": "PUNPRO BUSINESS",
    "currency_symbol": "$",
    "currency_code": "ARS",
    "db_path": "Z:\\punpro.db"
}
```

*Nota: Asegúrate de poner **dos barras diagonales invertidas (`\\`)** como en el ejemplo para evitar errores de ruta en Windows.*

5. Guarda el archivo y abre el programa. 

### ¡Felicidades! 🎉
El motor reconocerá instantáneamente que le estás pasando una ruta de red y se conectará directamente a la Caja 1. Cuando cobres un artículo en la Caja 2, la venta aparecerá en la Central de Auditoría (F3) de la Caja 1 en microsegundos gracias al motor de alta velocidad WAL integrado.
