# Cómo queda modularizado

Esta es la única nota de la raíz. No es la base de un módulo. Acá no van las reglas de cada pantalla.

Cuando se mejora un módulo, la mejora ya incluye esta forma. Se ofrece en la misma respuesta y se aplica. No queda un archivo suelto en la carpeta de arriba ni una nota nueva en la raíz.

## La pirámide

La base junta ramas. No lleva `plano.md`. Ejemplos de base: `src/cajero`, `src/admin`, `src`.

Una rama arranca en la primera carpeta propia del módulo. Ahí vive el código de esa rama y su `plano.md`.

Cada corte de adentro es una subcarpeta. La subcarpeta no repite el plano. Lleva `README.md`.

```
base/                         no lleva plano
  rama/                       acá arranca
    plano.md                  frente y fondo
    pieza.py
    subcarpeta/
      README.md               qué hace, qué función, cómo funciona
      pieza.py
      otra/
        README.md
```

Si un archivo está suelto al lado de carpetas, entra en la carpeta de su rama. La base no guarda piezas de una rama.

## plano.md

Va solo en la carpeta donde arranca la rama. Documenta los dos lados.

Frente: qué ve el usuario, qué tecla o botón lo abre, qué pinta y qué no pinta.

Fondo: qué función corre, en qué archivo, qué tabla toca, en qué orden, y qué no hay que romper.

Si el fondo vive en otra carpeta, el plano dice el camino. Esa otra carpeta, si es otra rama, tiene su propio `plano.md`. Si es subcarpeta, tiene `README.md`.

## README.md

Va en cada subcarpeta, con el máximo detalle que el código tiene hoy.

- Qué hace la carpeta.
- Qué función, con el nombre real.
- Cómo funciona, en el orden en que corre.
- Qué devuelve cuando falla.
- Qué no debe cambiar una mejora futura.

No se copia el plano entero. El README es de esa subcarpeta.

## Al mejorar un módulo

1. Leer `modularizacion.md` y el `plano.md` de la rama. Si se toca una subcarpeta, leer también su `README.md`.
2. Ofrecer esta opción en la respuesta: la rama queda en su carpeta, con `plano.md`, y cada subcarpeta con `README.md`.
3. Aplicarla en el mismo cambio. Si el módulo era un solo archivo en la base, pasa a su carpeta. Si ya estaba en carpeta, se actualizan el plano y el README de lo que se tocó.
4. No crear `regla_*.md` en la raíz.
5. Decir en qué carpeta quedó la nota.
