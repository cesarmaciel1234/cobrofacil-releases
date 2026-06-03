import sys
import tkinter as tk

def show_explosion(nombre, monto_str):
    nombre = str(nombre or "Cliente").strip()
    monto_str = str(monto_str or "$0.00").strip()
    if not nombre:
        nombre = "Cliente"
    if not monto_str:
        monto_str = "$0.00"

    root = tk.Tk()
    root.withdraw() # Oculta la ventana principal
    
    overlay = tk.Toplevel()
    overlay.attributes('-topmost', True)
    overlay.overrideredirect(True)
    overlay.configure(bg='#070b12')
    
    # Dimensiones y posicionamiento en la esquina inferior derecha (estilo Toast)
    sw = overlay.winfo_screenwidth()
    sh = overlay.winfo_screenheight()
    width = 380
    height = 110
    x = sw - width - 20
    y = sh - height - 60 # Encima de la barra de tareas
    
    overlay.geometry(f"{width}x{height}+{x}+{y}")
    
    # Elevar ventana pero SIN forzar foco para mantener la operación del cajero en segundo plano
    overlay.lift()

    try:
        import winsound
        winsound.Beep(880, 100)
        winsound.Beep(1109, 150)
    except:
        pass

    canvas = tk.Canvas(overlay, bg='#070b12', highlightthickness=1, highlightbackground='#00b1ea')
    canvas.pack(fill='both', expand=True)

    # --- DISEÑO TOAST PREMIUM ---
    # Icono MP (Círculo azul con destello)
    canvas.create_oval(15, 20, 75, 80, fill='#001b2e', outline='#00b1ea', width=2)
    canvas.create_text(45, 50, text="MP", font=('Segoe UI Black', 20), fill='#00b1ea')

    # Textos de notificación
    canvas.create_text(90, 25, text="PAGO DETECTADO", font=('Segoe UI', 10, 'bold'), fill='#00ff88', anchor='w')
    canvas.create_text(90, 52, text=monto_str, font=('Segoe UI Black', 24), fill='#ffffff', anchor='w')
    canvas.create_text(90, 85, text=f"DE: {nombre.upper()}", font=('Segoe UI', 10, 'bold'), fill='#94a3b8', anchor='w')

    # Cierra al hacer clic o tras 5 segundos
    overlay.bind("<Button-1>", lambda e: root.destroy())
    overlay.after(5000, lambda: root.destroy())

    root.mainloop()

if __name__ == "__main__":
    nombre_cliente = sys.argv[1] if len(sys.argv) > 1 else "Cliente"
    monto_pago = sys.argv[2] if len(sys.argv) > 2 else "$0.00"
    show_explosion(nombre_cliente, monto_pago)
