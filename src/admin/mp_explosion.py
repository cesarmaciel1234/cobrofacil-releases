import sys
import tkinter as tk
import random
import math

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
    overlay.attributes('-fullscreen', True)
    overlay.attributes('-topmost', True)
    overlay.overrideredirect(True)
    overlay.configure(bg='#000000')
    
    # Asegura que esté por encima de todo
    overlay.lift()
    overlay.focus_force()

    try:
        import winsound
        winsound.Beep(1000, 150)
        winsound.Beep(1200, 150)
    except:
        pass

    canvas = tk.Canvas(overlay, bg='#000000', highlightthickness=0)
    canvas.pack(fill='both', expand=True)

    sw = overlay.winfo_screenwidth()
    sh = overlay.winfo_screenheight()

    # --- GLOW DE FONDO ---
    center_x, center_y = sw // 2, sh // 2
    for i in range(30, 0, -1):
        r = int(0 + (30-i) * 0.8)
        g = int(20 + (30-i) * 1.5)
        b = int(10 + (30-i) * 0.5)
        color = f'#{r:02x}{g:02x}{b:02x}'
        radius = i * (max(sw, sh) // 30)
        canvas.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            fill=color, outline=''
        )

    # --- PARTÍCULAS ---
    particles = []
    colors = ['#00b1ea', '#00d2ff', '#e0f2fe', '#ffffff', '#cbd5e1']
    
    # Explosión (Hacia afuera)
    for _ in range(400):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(4, 25)
        size = random.randint(10, 20)
        color = random.choice(colors)
        
        p_id = canvas.create_text(
            center_x, center_y,
            text=monto_str,
            font=('Arial', size, 'bold'),
            fill=color,
            anchor='center'
        )
        particles.append({
            'id': p_id, 'x': center_x, 'y': center_y,
            'vx': math.cos(angle) * speed, 'vy': math.sin(angle) * speed,
            'gravity': 0.18, 'life': 1.0, 'decay': random.uniform(0.008, 0.02)
        })

    # Lluvia (Hacia abajo)
    for _ in range(200):
        x = random.randint(0, sw)
        y = random.randint(-sh, 0)
        speed = random.uniform(3, 8)
        size = random.randint(8, 16)
        color = random.choice(['#00b1ea', '#00d2ff', '#ffffff'])
        
        p_id = canvas.create_text(
            x, y,
            text=monto_str,
            font=('Arial', size),
            fill=color,
            anchor='center'
        )
        particles.append({
            'id': p_id, 'x': x, 'y': y,
            'vx': random.uniform(-1, 1), 'vy': speed,
            'gravity': 0, 'life': 1.0, 'decay': 0, 'type': 'rain'
        })

    # --- PLACA CENTRAL DE AISLAMIENTO Y BRILLO (PREMIUM GLOW CARD - 2026 HYPER CLEAR EDITION) ---
    card_w = max(780, int(sw * 0.58))
    card_h = 390
    
    cx, cy = center_x, center_y + 15
    x1, y1 = cx - card_w // 2, cy - card_h // 2
    x2, y2 = cx + card_w // 2, cy + card_h // 2
    r = 30 # Radio de redondeado
    
    # 1. Aura de brillo degradado (Cyan/Ice Blue Glow concéntrico)
    for i in range(15, 0, -3):
        canvas.create_polygon(
            [x1-i, y1-i, x1-i, y1-i, x2+i, y1-i, x2+i, y1-i, x2+i, y2+i, x2+i, y2+i, x1-i, y2+i, x1-i, y2+i, x1-i, y1-i],
            fill='', outline='#005b8a', width=2, smooth=True
        )
        
    # 2. Fondo sólido oscuro y borde de neón brillante Cyan 2026 (Para bloquear la lluvia de partículas)
    points = [
        x1+r, y1, x1+r, y1,
        x2-r, y1, x2-r, y1,
        x2, y1, x2, y1+r, x2, y1+r,
        x2, y2-r, x2, y2-r,
        x2, y2, x2-r, y2, x2-r, y2,
        x1+r, y2, x1+r, y2,
        x1, y2, x1, y2-r, x1, y2-r,
        x1, y1+r, x1, y1+r,
        x1, y1
    ]
    canvas.create_polygon(points, fill='#070b12', outline='#00b1ea', width=5, smooth=True)

    # --- TEXTO CENTRAL ---
    # Sombra/Brillo Neon Cyan de Fondo para el Monto
    main_amount_glow = canvas.create_text(
        center_x + 3, center_y - 57,
        text=monto_str, font=('Arial', 150, 'bold'), fill='#00d2ff', anchor='center'
    )
    
    # Monto Principal en Blanco Puro/Cristalino (Súper legible y limpio)
    main_amount = canvas.create_text(
        center_x, center_y - 60,
        text=monto_str, font=('Arial', 150, 'bold'), fill='#ffffff', anchor='center'
    )
    
    # Estado en Verde Neón Vibrante (Aprobado / Éxito)
    canvas.create_text(
        center_x, center_y + 60,
        text="PAGO RECIBIDO", font=('Arial', 50, 'bold'), fill='#00ff88', anchor='center'
    )
    
    # Cliente en Plata/Blanco Claro
    canvas.create_text(
        center_x, center_y + 130,
        text=f"DE: {nombre.upper()}", font=('Arial', 28, 'bold'), fill='#cbd5e1', anchor='center'
    )

    canvas.create_text(
        center_x, sh - 50,
        text="PRESIONE PARA CERRAR • PUNPRO SMART BUSINESS", font=('Arial', 14, 'bold'), fill='#334155', anchor='center'
    )

    frame_count = [0]
    def update_animation():
        if not overlay.winfo_exists(): return
        frame_count[0] += 1
        
        for p in particles:
            if p.get('type') == 'rain':
                p['y'] += p['vy']
                if p['y'] > sh:
                    p['y'] = -20
                    p['x'] = random.randint(0, sw)
            else:
                p['x'] += p['vx']
                p['y'] += p['vy']
                p['vy'] += p['gravity']
                p['life'] -= p['decay']
                if p['life'] <= 0:
                    canvas.itemconfig(p['id'], state='hidden')
            canvas.coords(p['id'], p['x'], p['y'])

        # Efecto de pulso en el texto central (Monto y su sombra de brillo)
        pulse = 1.0 + 0.05 * math.sin(frame_count[0] * 0.15)
        new_size = int(150 * pulse)
        canvas.itemconfig(main_amount_glow, font=('Arial', new_size, 'bold'))
        canvas.itemconfig(main_amount, font=('Arial', new_size, 'bold'))
        
        # Efecto de destello inicial (White/Cyan 2026 Ice Theme)
        if frame_count[0] < 4: canvas.configure(bg='#ffffff')
        elif frame_count[0] < 8: canvas.configure(bg='#00b1ea')
        elif frame_count[0] == 8: canvas.configure(bg='#000000')

        overlay.after(16, update_animation)

    update_animation()

    # Cierra la ventana al hacer clic, apretar Escape, o tras 6 segundos
    overlay.bind("<Button-1>", lambda e: root.destroy())
    overlay.bind("<Escape>", lambda e: root.destroy())
    overlay.after(6000, lambda: root.destroy())

    root.mainloop()

if __name__ == "__main__":
    nombre_cliente = sys.argv[1] if len(sys.argv) > 1 else "Cliente"
    monto_pago = sys.argv[2] if len(sys.argv) > 2 else "$0.00"
    show_explosion(nombre_cliente, monto_pago)
