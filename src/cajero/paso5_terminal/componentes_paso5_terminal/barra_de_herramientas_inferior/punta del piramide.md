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
    cobrar.py              F12, al final, mismo color que las demás
    fila.py                F1 F3 F4 F5 F6 F7 F8 F11 y después F12
  bloquear/                candado
  chatbot/                 botón del asistente
```

El chat y el teclado en pantalla siguen en `componentes_barra_inferior/chatbot` y `componentes_barra_inferior/teclado_virtual`. Esta barra solo los llama. El asistente es un panel de la venta: no usa el navegador de la cartelería ni abre otra ventana. No se crea hasta el primer clic. A los 2 s el cursor vuelve al buscador. Un escaneo o F12 lo cierra. El detalle está en `src/cajero/README.md`, sección «El paso 5 es dueño de la venta».

El terminal sigue usando `BarraDeHerramientasInferior`, `actualizar_texto_espera` y `set_tema_texto`.
