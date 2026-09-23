# Punta de la pirámide — barra de herramientas

La franja de teclas del cajero. Esta carpeta la arma. No cobra ni abre el teclado: solo muestra los botones.

```
barra_de_herramientas_inferior/
  punta del piramide.md
  barra.py                 junta la franja
  teclado/                 botón TECLADO
  tema/                    botón TEMAS
  version/                 COBRO FACIL
  espera/                  tickets en espera
  atajos/
    tecla.py               una tecla F
    cobrar.py              F12, al final, en azul
    fila.py                F1 F3 F4 F5 F6 F7 F8 F11 y después F12
  bloquear/                candado
  chatbot/                 botón del asistente
```

El chat completo y el teclado en pantalla siguen en `componentes_barra_inferior/chatbot` y `componentes_barra_inferior/teclado_virtual`. Esta barra solo los llama.

El terminal sigue usando `BarraDeHerramientasInferior`, `actualizar_texto_espera` y `set_tema_texto`.
