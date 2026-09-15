# LOGICA DE SEGURIDAD: DETECCION INTELIGENTE DE APERTURA DE CAJON

Para evitar falsas alarmas y detectar robos reales, el sistema diferencia entre **Apertura por Software** y **Apertura por Hardware**.

## 1. Detección por Software (Ventas Legales)
Cuando se registra una venta, el sistema evalúa el método de pago:
- Si es **SOLO EFECTIVO**: El sistema asume que la caja se abrirá (Apertura Legal).
- Si es **TARJETA / TRANSFERENCIA**: El sistema asume que la caja NO debe abrirse.

## 2. Detección por Hardware (Sensor Físico)
Si el TPV tiene activado el "Modo Hardware", un sensor físico avisa al CerebroNexus en el milisegundo exacto en que el cajón se abre físicamente.

## 3. Matriz de Decisión (El Algoritmo de Alarma)
Cuando el CerebroNexus recibe la señal del sensor físico de que el cajón se abrió, verifica quién está en la pantalla y por qué se abrió:

| Perfil en Pantalla | Hubo Venta en Efectivo (últimos 5 seg)? | Resultado / Acción del Sistema |
|-------------------|---------------------------------------|--------------------------------|
| **CAJERO**        | SI                                    | ✅ **OK** (Registro normal) |
| **CAJERO**        | NO                                    | 🚨 **ALERTA CRÍTICA**: Cajón abierto sin venta. |
| **ADMIN / JEFE**  | NO                                    | 🔑 **INTERVENCIÓN**: Prueba de hardware o auditoría. |
| **NADIE (Bloqueado)** | NO                                | 🚨 **ALERTA ROJA**: Violación física del cajón. |

## 4. ¿Por qué el Admin no genera alarma?
Como el Administrador y el Jefe a veces necesitan realizar un "Test de Caja" (probar si la gaveta abre o no), la apertura física bajo su perfil no se marca como ROBO, sino como INTERVENCIÓN / PRUEBA. El cajero, en cambio, NUNCA debe abrir la caja si no hay dinero de por medio.
