# Registro de Errores Críticos y Soluciones

Este documento sirve como bitácora técnica para registrar los bugs difíciles que hemos solucionado. El objetivo es **no volver a tropezar con la misma piedra** y tener un manual de supervivencia para el futuro.

---

## 1. Problema de Detección en Red (Radar Multicaja)
**Fecha de registro**: Junio 2026

### ❌ El Error (Síntomas)
- Al escanear la red desde la ventana "Servidor Multicaja", la PC Esclava o la Notebook no detectaban la IP de la PC Maestra.
- Ocurría el fenómeno de "detección de un solo lado" (Ejemplo: La PC2 detectaba a la Notebook, pero la Notebook no leía a la PC2).

### 🔍 La Causa Técnica
Descubrimos **tres fallos** que, combinados, bloqueaban la conexión:

1. **Método de Escaneo Lento**: El sistema original usaba un escáner de puertos TCP puerto por puerto (intentando conectar al puerto 3306). Esto era extremadamente lento y Windows lo bloqueaba casi siempre por seguridad.
2. **Permisos de Firewall Silenciados**: Al intentar otorgar permisos de Administrador (UAC) para abrir los puertos, el sistema fallaba en segundo plano porque ejecutaba `sys.executable` (solo python) sin apuntar al script `main.py`. La ventana amarilla/azul de permisos nunca aparecía.
3. **Reglas de Firewall Antiguas (El gran culpable)**: Si el cliente ya había instalado una versión vieja del sistema, el Windows Firewall ya tenía guardada la regla `TPV_CajaFacil_TCP`. Al existir, el sistema *omitía* pedir permisos de nuevo, y por lo tanto **nunca abría el puerto UDP 37020** que construimos para el nuevo Radar de Descubrimiento Rápido.

### ✅ La Solución Implementada
1. **Nuevo Radar UDP**: Cambiamos el escaneo TCP puerto por puerto por un sistema de **Broadcast UDP** (Puerto 37020). Es instantáneo y estándar en la industria.
2. **Forzado de Firewall (_v3)**: Renombramos la regla del firewall internamente a `TPV_CajaFacil_TCP_v3` y `TPV_CajaFacil_UDP_v3`. Al cambiar el nombre, **obligamos** a Windows a solicitar nuevamente permisos al usuario al abrir la App, asegurando que los nuevos puertos UDP se abran correctamente en cualquier PC.
3. **Corrección de la llamada UAC**: Reparamos el comando de elevación en `mariadb_controller.py` añadiéndole `os.path.abspath(sys.argv[0])` para que sepa exactamente a qué archivo darle permisos.

---

## 2. Motor de Base de Datos Ausente (La PC Nueva no encendía DB)
**Fecha de registro**: Junio 2026

### ❌ El Error (Síntomas)
- Al llevar la instalación compilada (el ZIP) a una "PC Nueva" e intentar usarla como Maestra, la base de datos se quedaba congelada y "no se encendía".

### 🔍 La Causa Técnica
- El script de empaquetado para generar la versión final a los clientes (`empaquetar_para_firebase.py`) **no estaba incluyendo la carpeta `mariadb_server`** dentro del ZIP.
- El usuario copiaba el sistema a la PC Nueva, pero literalmente le faltaba el "motor" local de la base de datos. Sin ese motor físico, no había nada que encender.

### ✅ La Solución Implementada
- Modificamos `empaquetar_para_firebase.py` para que lea y copie dinámicamente toda la carpeta `mariadb_server/` al comprimir el ZIP final (`CobroFacilPOS_v3.zip`). 
- Ahora, cada vez que se compila y empaqueta el programa, el motor de la base de datos viaja de forma nativa.
