# Bandeja del Lanzador (`src/lanzador/bandeja`)

Qué hace: mantiene el Lanzador Maestro residente en la bandeja del sistema (`--background` o al cerrar `✕` para minimizar) como supervisor liviano del Servidor fantasma y de caídas de perfiles.

Qué función: `instalar_bandeja_lanzador`, `ControladorBandejaLanzador`.

Cómo funciona:
- Al iniciar con `--background` o al apretar `✕`, oculta el Hub en bandeja sin tumbar el proceso `--server`.
- Registra el marcador `locks/lanzador_maestro.bandeja` y escucha `locks/lanzador_maestro.mostrar` cada 200 ms: si el operador abre el acceso directo de Cobro Fácil, muestra el Lanzador al frente al instante sin lanzar otra instancia.
- Permite salir explícitamente desde **Salir del Lanzador** en el menú contextual; aun saliendo del Lanzador, el Servidor fantasma (`--server`) sigue corriendo independiente.
