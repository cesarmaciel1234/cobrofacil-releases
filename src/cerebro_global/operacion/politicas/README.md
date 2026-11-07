# Políticas operativas

## Qué hace la carpeta

Guarda reglas explícitas y versionadas para que el cerebro no esconda decisiones de negocio en código.

## Qué función, con el nombre real

* `obtener(db, codigo)`: devuelve la última política activa o su base segura.
* `guardar(db, codigo, reglas, version)`: publica una versión nueva.

## Cómo funciona

La política inicial `COMPRA_AUTONOMA` deja toda propuesta en borrador y exige revisión. Las siguientes etapas podrán agregar topes, mínimos de proveedor y categorías autorizadas.

## Qué devuelve cuando falla

`obtener` retorna la política segura por defecto; `guardar` devuelve falso.

## Qué no debe cambiar una mejora futura

Una política no autoriza por sí misma cambios de stock ni despacho de WhatsApp.
