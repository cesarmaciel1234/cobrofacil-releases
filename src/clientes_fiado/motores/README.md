# Motores

Estas carpetas reexportan las clases para no romper el camino viejo. El código está en el garante y en la oficina.

| Carpeta de acá | Clase | Dónde vive |
|---|---|---|
| `cuenta/` | `MotorCuenta` | `oficina/cuenta/motor.py` |
| `fiado/` | `MotorFiadoExpress` | `garante/fiado/motor.py` |
| `cliente/` | `MotorClienteExpress` | `garante/cuenta_corriente/motor.py` |

Ninguna imprime el ticket ni abre el cajón. Fiado y Cuenta corriente no se llaman entre sí. Los dos usan la oficina.
