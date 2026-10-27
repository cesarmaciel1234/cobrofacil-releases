# Ventana del servidor

Lo que se ve del proceso `--server`. No decide el puesto y no toca la base.

## Qué hace la carpeta
Arma la ventana y el icono de la bandeja. `bandeja.py` la muestra, la vigila y la apaga.

## Qué función, con el nombre real
* `armar_lienzo(esclava)` en `lienzo.py`: devuelve la ventana, la consola y `poner_estado`. El título de Windows es `Servidor Cobro Fácil`, el mismo texto que busca el lanzador. Adentro, la pastilla dice ESCLAVA o MAESTRA.
* `Tablero` en `tablero.py`: seis paneles con borde propio. Arriba, `punpro.db` y `espejo_tienda.db`. Al medio, `cola_tickets` y `cola_cambios`. Abajo, la bitácora y la auditoría de stock. Las colas salen de los JSON cada 3 segundos. Esta ventana no las reenvía: las sube el oficio de la esclava. Las bases y la auditoría se leen en solo lectura.
* `Grilla` en `grilla.py`: la tabla. No se edita.
* `vigia.py`: `filas_tickets`, `filas_cambios`, `filas_auditoria`, `catalogo`, `canal`, `acortar`. `catalogo` no abre MariaDB. `filas_auditoria` lee `auditorias_inventario` en `punpro.db` y en la réplica. Un conteo nuevo también deja una línea en la bitácora. No se reenvía y no entra en `cola_cambios`.
* `presencia.py`: `arrancar` y `foto`. La pastilla dice si la maestra está en línea o desconectada (puerto 3306, sin abrir la base). Al lado, el nombre de cada PC que avisa por UDP 37021, con el rol `maestra`, `reserva` o `esclava`. El puerto se comparte con Nexus. Esta PC no se lista a sí misma. Si el aviso es `DATOS` y trae `server_ip`, la esclava sigue esa IP. Después sube la cola, baja el espejo y refresca la tele, y no lo reenvía.
* `pedir_clave(parent, aviso)` en `clave.py`: apagar pide la clave. `pin_servidor()` lee `servidor_clave` en la config, y si no está usa `1234`. El diálogo no muestra esa clave. Si la ventana está oculta, primero se muestra: un diálogo hijo de una ventana oculta no aparece y el proceso queda trabado.
* `icono_bandeja(esclava)`: cuadrado azul con E, o verde con S, si no hay `pos_icon.png`. El aviso de Windows usa `src/assets/servidor.ico`, la misma ruta que el ejecutable empaqueta. No se copia a AppData.
* `hoja_menu()`: el clic derecho de la bandeja. El tema del día pinta `QWidget` de azul y el menú quedaba como un enlace. Esta hoja lo deja en el mismo tono que la consola. En esclava dice «Mostrar espejo» y «Apagar espejo».

## Cómo funciona, en el orden en que corre
1. `bandeja.py` pregunta el oficio y llama a `armar_lienzo`.
2. La ventana se muestra en los dos puestos. No se esconde sola. El cuadrado de la barra la estira a toda la pantalla y la devuelve.
3. Cerrar o «Ocultar en bandeja» la esconde. El cierre no corre `hide()` en el mismo evento: eso dejaba el cliente en blanco. No pide clave y no espera el conteo de la base: ese conteo va en el hilo `ventana-base`. El proceso sigue. Al volver a mostrarla, `reanudar()` retoma las tablas.
4. «Apagar servidor» abre `pedir_clave`. Sin la clave el proceso sigue. Con la clave, `bandeja.py` lo apaga.
5. Cada vuelta del espejo y de la cartelería escribe una línea (`espejo  …`, `carteleria  …`). Si falla, la línea es un aviso y la copia o la caché quedan.

## Qué devuelve cuando falla
Si no hay icono en disco, pinta el cuadrado. No lanza.

## Qué no debe cambiar una mejora futura
* No ocultar la ventana al arrancar: en esclava el usuario no ve el icono de Windows y el puesto parece que no existe.
* El título de Windows y `focus_existing_store_server` usan la misma constante, `Servidor Cobro Fácil`. Si cambia uno, cambia el otro. El lanzador no llama a `ShowWindow` sobre una ventana oculta: escribe `locks/servidor_tienda.mostrar` y el proceso se muestra solo. Enganchar el hilo de Windows del lanzador al del servidor la deja blanca y trabada.
* No prender MariaDB ni refrescar el espejo desde acá. Eso es `oficio/`.
* No escribir la clave en el log. `pedir_clave` solo dice si se aceptó o se canceló.
* El candado `locks/servidor_tienda.lock` solo vale si el PID es `python.exe`, `pythonw.exe` o `cobrofacil_pos.exe` y además trae `--server`. La consola de Windows también escribe `--server` en su línea y no es el espejo.
