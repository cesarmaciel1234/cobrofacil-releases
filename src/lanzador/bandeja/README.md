# Bandeja del Lanzador (`src/lanzador/bandeja`)

Qué hace: mantiene el Lanzador Maestro residente en la bandeja del sistema (`--background` o al cerrar `✕` para minimizar) como supervisor liviano del Servidor fantasma y de caídas de perfiles.

Qué función: `instalar_bandeja_lanzador`, `ControladorBandejaLanzador`.

Cómo funciona:
- Al iniciar con `--background` o al apretar `✕`, oculta el Hub en bandeja sin tumbar el proceso `--server`.
- Registra `locks/lanzador_maestro.tray` y escucha `locks/lanzador_maestro.mostrar` cada 200 ms: si el operador abre el acceso directo de Cobro Fácil, muestra el Lanzador al frente al instante sin duplicar instancia.
- Permite activar con 1 clic (UAC) el **Servicio Windows (Session 0)** para que el servidor arranque incluso antes de iniciar sesión en Windows, o salir solo del Lanzador con **Salir del Lanzador** sin apagar el servidor.
