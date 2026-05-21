# 📦 Plan de Empaquetado: PunPro POS Elite

Este plan detalla los pasos para convertir el código fuente de Python en un archivo ejecutable (.exe) profesional listo para usar en cualquier computadora con Windows.

## 1. Preparación del Entorno
Es necesario instalar **PyInstaller**, la herramienta estándar para empaquetar aplicaciones Python.

```bash
pip install pyinstaller
```

## 2. Configuración de Recursos
La aplicación utiliza archivos externos que deben incluirse en el ejecutable o estar presentes en la carpeta:
- `src/styles.qss`: Estilos visuales.
- `config.json`: Configuración inicial.
- `punpro.db`: Base de datos (el sistema la crea si no existe, pero es bueno tener un respaldo).

## 3. Script de Empaquetado (`package.bat`)
He creado un script automatizado para generar el ejecutable con un solo clic. Este script:
1. Limpia carpetas anteriores (`build`, `dist`).
2. Ejecuta PyInstaller con los parámetros óptimos para PyQt5.
3. Incluye los archivos de soporte necesarios.

## 4. Estructura de Salida
Tras el proceso, la carpeta `dist/PunPro` contendrá:
- `PunPro.exe`: El programa principal.
- Librerías necesarias (PyQt5, sqlite3, etc.).
- Carpeta `src/` con el archivo `styles.qss`.

## 🚀 Próximos Pasos
1. **Crear el archivo `package.bat`** (ya disponible en el directorio raíz).
2. **Ejecutarlo** y verificar que el `.exe` abre correctamente.
3. **Inno Setup (Opcional)**: Si deseas un instalador con "Siguiente, Siguiente", podemos usar esta herramienta gratuita una vez tengamos el ejecutable.
