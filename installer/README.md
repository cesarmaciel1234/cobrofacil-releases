# 🏆 CajaFácil Pro — Instalador

## ¿Qué es esto?

El instalador es parte del mismo proyecto principal pero compilado de forma independiente.
Cuando el cliente lo ejecuta, **descarga la app directamente de GitHub** y la instala.
El código fuente nunca se expone.

---

## Estructura

```
installer/
├── installer_build.py   ← Código fuente del instalador (Python + tkinter)
├── build.bat            ← Compilar el .exe con doble clic
└── README.md            ← Este archivo
```

---

## Cómo funciona

```
Vos compilás → CobroFacil_POS_Setup.exe (10 MB)
                        ↓
Cliente ejecuta el .exe
                        ↓
Descarga CobroFacil_POS.zip de GitHub (cobrofacil-releases)
                        ↓
Instala en C:\Cobro Fácil POS
Instala Python 3.11 si no tiene
Instala dependencias (PyQt5, etc.)
Crea acceso directo en escritorio
Limpia temporales
                        ↓
Cliente abre el programa ✅
```

---

## Cómo compilar un nuevo instalador

Desde la **carpeta raíz del proyecto** (no desde installer/):

```
Doble clic en installer\build.bat
```

O desde consola:
```bat
.venv\Scripts\pyinstaller.exe --onefile --windowed --name CobroFacil_POS_Setup --distpath .\dist_installer --workpath .\build_installer --specpath .\build_installer installer\installer_build.py
```

Resultado: `CobroFacil_POS_Setup.zip` en la raíz del proyecto.

---

## Cuándo recompilar el instalador

Solo necesitás recompilar si cambiás:
- La URL de descarga (`DOWNLOAD_URL`)
- La carpeta de instalación (`DESTINO`)
- El diseño visual del instalador
- La versión de Python objetivo

**Para actualizaciones normales de la app → NO recompilás el instalador.**
Solo subís el nuevo ZIP al release de GitHub.

---

## Flujo completo de una nueva versión

```
1. Hacés cambios en el código
2. git add . && git commit -m "descripcion" && git push
3. python scratch\crear_zip.py  →  CobroFacil_POS_v2026.x.x.zip
4. Subir ese ZIP a cobrofacil-releases como nuevo release
   (renombrarlo a CobroFacil_POS.zip al subir)
5. Los clientes existentes se actualizan solos al cerrar caja
6. Clientes nuevos usan CobroFacil_POS_Setup.exe (no cambia)
```

---

## Repos GitHub

| Repo | Visibilidad | Contenido |
|------|------------|-----------|
| `cobrofacil-pro` | 🔒 Privado | Código fuente |
| `cobrofacil-releases` | 🌐 Público | ZIP de distribución |
