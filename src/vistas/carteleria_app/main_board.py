import os
import random
import logging
import urllib.request
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QGridLayout, QLabel
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPixmap

# Componentes modulares
from src.vistas.carteleria_app.theme import C_THEME
from src.vistas.carteleria_app.info_negocio import InfoNegocio
from src.vistas.carteleria_app.mensaje import Mensaje
from src.vistas.carteleria_app.pantalla1 import Pantalla1
from src.vistas.carteleria_app.pantalla2 import Pantalla2
from src.vistas.carteleria_app.pantalla3 import Pantalla3
from src.vistas.carteleria_app.pantalla4 import Pantalla4
from src.vistas.carteleria_app.alerta_sos import AlertaSOS
from src.vistas.carteleria_app.banderin import BanderinVolador
from src.vistas.carteleria_app.motor_ia import MotorIA

try:
    from src.base_de_datos.database import Database
except ImportError:
    Database = None

logger = logging.getLogger("Carteleria_Autonoma")

class CarteleriaMain(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout_mode = 4 
        self.img_index = 0
        self.datos_destacados = []
        self.combos_relacionados = [
            ("Asado de Novillo", "Carbón 4kg y Limón fresco"),
            ("Vacío", "Provoleta y Pan de Campo"),
            ("Pechito de Cerdo", "Salsa BBQ y Papas Fritas")
        ]
        
        # --- FONDO macOS ---
        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)
        img_path = os.path.join(os.path.dirname(__file__), "..", "assets", "macos_bg.png")
        if os.path.exists(img_path):
            self.bg_label.setPixmap(QPixmap(img_path))
        else:
            self.setStyleSheet(f"background-color: {C_THEME['bg']};")

        # --- INSTANCIAR ZONAS MODULARES ---
        self.info_negocio = InfoNegocio()
        self.info_negocio.btn_modo.clicked.connect(self._ciclar_layout)
        
        self.mensaje = Mensaje()
        self.zona1_carrusel = Pantalla1()
        self.zona2_precios = Pantalla2()
        self.zona3_extra1 = Pantalla3()
        self.zona4_extra2 = Pantalla4()
        
        self._build_ui()
        
        # ⏱️ TIMER ROTACIÓN PROMOCIONES
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._actualizar_pantallas_promocionales)
        self.timer.start(16000) 
        
        self.timer_db = QTimer(self)
        self.timer_db.timeout.connect(self._sincronizar_todo_con_db)
        self.timer_db.start(10000)

        self.clima_pilar = ("sol", "22°C Pilar")
        self._obtener_clima()
        self.timer_clima = QTimer(self)
        self.timer_clima.timeout.connect(self._obtener_clima)
        self.timer_clima.start(3600000)

        self.timer_vuelo = QTimer(self)
        self.timer_vuelo.timeout.connect(lambda: self.banderin.lanzar(self.datos_destacados))
        self.timer_vuelo.start(35000) 
        
        self._sincronizar_todo_con_db() 

    def resizeEvent(self, event):
        self.bg_label.resize(self.size())
        super().resizeEvent(event)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        
        # --- PANTALLA NORMAL ---
        self.page_normal = QWidget()
        self.page_normal.setStyleSheet("background: transparent;")
        lay_normal = QVBoxLayout(self.page_normal)
        lay_normal.setContentsMargins(20, 20, 20, 20)
        
        lay_normal.addWidget(self.info_negocio)
        
        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: transparent;")
        self.grid = QGridLayout(self.grid_container)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(20)
        lay_normal.addWidget(self.grid_container, 1)
        
        lay_normal.addWidget(self.mensaje)
        
        # --- PANTALLA SOS ---
        self.page_sos = AlertaSOS()

        self.stack.addWidget(self.page_normal)
        self.stack.addWidget(self.page_sos)
        root.addWidget(self.stack)

        # 🛸 WIDGET FLOTANTE MODULARIZADO
        self.banderin = BanderinVolador(self)
        
        self._aplicar_layout()

    def _ciclar_layout(self):
        self.layout_mode += 1
        if self.layout_mode > 4:
            self.layout_mode = 1
        self._aplicar_layout()

    def _aplicar_layout(self):
        for i in reversed(range(self.grid.count())): 
            w = self.grid.itemAt(i).widget()
            if w:
                self.grid.removeWidget(w)
            
        for i in range(4): self.grid.setColumnStretch(i, 0)
        self.grid.setRowStretch(0, 0)
        self.grid.setRowStretch(1, 0)
            
        if self.layout_mode == 1:
            self.grid.addWidget(self.zona2_precios, 0, 0)
            self.grid.setColumnStretch(0, 1)
        elif self.layout_mode == 2:
            self.grid.addWidget(self.zona1_carrusel, 0, 0)
            self.grid.addWidget(self.zona2_precios, 0, 1)
            self.grid.setColumnStretch(0, 1)
            self.grid.setColumnStretch(1, 1)
        elif self.layout_mode == 3:
            self.grid.addWidget(self.zona1_carrusel, 0, 0)
            self.grid.addWidget(self.zona2_precios, 0, 1)
            self.grid.addWidget(self.zona3_extra1, 0, 2)
            self.grid.setColumnStretch(0, 1)
            self.grid.setColumnStretch(1, 1)
            self.grid.setColumnStretch(2, 1)
        elif self.layout_mode == 4:
            self.grid.addWidget(self.zona1_carrusel, 0, 0)
            self.grid.addWidget(self.zona2_precios, 0, 1) 
            self.grid.addWidget(self.zona3_extra1, 0, 2)
            self.grid.addWidget(self.zona4_extra2, 0, 3)
            self.grid.setColumnStretch(0, 1)
            self.grid.setColumnStretch(1, 1)
            self.grid.setColumnStretch(2, 1)
            self.grid.setColumnStretch(3, 1)
            
        self.grid.setRowStretch(0, 1) 
        self._actualizar_pantallas_promocionales()

    def _obtener_clima(self):
        try:
            import json
            # Coordenadas de Pilar, Buenos Aires
            url = "https://api.open-meteo.com/v1/forecast?latitude=-34.4587&longitude=-58.9142&current_weather=true"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                temp = data.get("current_weather", {}).get("temperature", 22)
                code = data.get("current_weather", {}).get("weathercode", 0)
                
                icon_name = "sol"
                if code in [1, 2, 3, 45, 48]:
                    icon_name = "nube"
                elif code >= 51:
                    icon_name = "lluvia"
                
                self.clima_pilar = (icon_name, f"{int(temp)}°C Pilar")
        except Exception as e:
            print(f"Error al obtener clima: {e}")

    def _sincronizar_todo_con_db(self):
        try:
            if Database:
                db = Database.get_instance()
                
                # --- LECTURA DE CONFIGURACIÓN (TICKET) ---
                try:
                    rows_config = db.execute("SELECT clave, valor FROM configuracion")
                    cfg = {r[0]: r[1] for r in rows_config} if rows_config else {}
                    nombre_negocio = cfg.get("negocio_nombre", "Carnicería")
                    telefono_negocio = cfg.get("negocio_telefono", "No disponible")
                    
                    self.info_negocio.actualizar_nombre(nombre_negocio)
                    msg_publicitario = f"👨‍👩‍👧‍👦 ¡La mejor calidad para disfrutar en familia! Más de 500 familias nos eligen cada semana. ¡Gracias por su apoyo! ❤️ | Consultas por WhatsApp al: {telefono_negocio}"
                    self.mensaje.actualizar_texto(msg_publicitario)
                except Exception as e:
                    logger.warning(f"Error cargando info negocio desde DB: {e}")
                
                sos_query = "SELECT nombre, precio FROM productos WHERE es_sos = 1 AND precio > 0 LIMIT 1"
                oferta_sos = db.execute(sos_query)
                if oferta_sos:
                    nombre, precio = oferta_sos[0]
                    self.page_sos.actualizar(nombre, precio)
                    if self.stack.currentIndex() != 1:
                        self.stack.setCurrentIndex(1)
                else:
                    if self.stack.currentIndex() != 0:
                        self.stack.setCurrentIndex(0)
                
                precios_query = "SELECT categoria, nombre, precio FROM productos WHERE precio > 0 ORDER BY categoria"
                rows_precios = db.execute(precios_query)
                if rows_precios:
                    self.zona2_precios.set_items(self._agrupar(rows_precios))
                
                destacados_query = "SELECT nombre, precio FROM productos WHERE es_destacado = 1"
                rows_destacados = db.execute(destacados_query)
                if rows_destacados:
                    self.datos_destacados = rows_destacados
                else:
                    self._cargar_destacados_demo()
            else:
                self._cargar_demo_completa()
                
        except Exception as e:
            logger.warning(f"Simulando Base de Datos: {e}")
            self._cargar_demo_completa()

    def _actualizar_pantallas_promocionales(self):
        if not self.datos_destacados: return
        
        self.img_index = (self.img_index + 1) % len(self.datos_destacados)
        prod_actual = self.datos_destacados[self.img_index]
        
        # --- PANTALLA 1 (Zona 1): Alternar Especial vs Top 10 ---
        if random.choice([True, False]):
            self.zona1_carrusel.actualizar_especial(prod_actual[0], prod_actual[1])
        else:
            top10 = self.datos_destacados[:10]
            self.zona1_carrusel.actualizar_top10(top10)
            
        if len(self.datos_destacados) > 1:
            prod_siguiente = self.datos_destacados[(self.img_index + 1) % len(self.datos_destacados)]
            
            # --- PANTALLA 3 (Zona 3): Alternar Destacada vs Combo ---
            if random.choice([True, False]):
                self.zona3_extra1.actualizar_destacada(prod_siguiente[0], prod_siguiente[1])
            else:
                centro_compra_simulado = random.choice(["Asado", "Pechito de Cerdo", "Vacío", "Bondiola"])
                combo_sugerido = random.choice([
                    "Carbón 4kg y Limón fresco",
                    "Provoleta y Pan de Campo",
                    "Salsa BBQ y Papas Fritas",
                    "Chorizo Puro Cerdo y Chimichurri"
                ])
                self.zona3_extra1.actualizar_combo(centro_compra_simulado, combo_sugerido)
            
            prod_tercero = self.datos_destacados[(self.img_index + 2) % len(self.datos_destacados)]
            
            # --- PANTALLA 4 (Zona 4): Alternar Recomendación vs IA ---
            if random.choice([True, False]):
                self.zona4_extra2.actualizar_recomendacion(prod_tercero[0], prod_tercero[1])
            else:
                db_instancia = Database.get_instance() if Database else None
                ia_msg, ia_prod, ia_precio = MotorIA.generar_recomendacion(db_instancia, self.clima_pilar, self.datos_destacados)
                self.zona4_extra2.actualizar_ia(ia_msg, ia_prod, ia_precio, self.clima_pilar)

    # ── SIMULACIÓN DE DATOS ──
    def _agrupar(self, rows):
        agrupado = {}
        for cat, nombre, precio in rows:
            categoria = cat if cat else "Otros"
            if categoria not in agrupado: agrupado[categoria] = []
            agrupado[categoria].append((nombre, precio))
        return agrupado

    def _cargar_destacados_demo(self):
        # 10 productos para que el Top 10 esté lleno
        self.datos_destacados = [
            ("Asado de Novillo", 7500),
            ("Ojo de Bife Madurado", 12500),
            ("Matambre de Cerdo", 8500),
            ("Chorizo Casero", 4500),
            ("Costillar Especial", 6800),
            ("Vacío Seleccionado", 8200),
            ("Bondiola Entera", 7200),
            ("Entraña Fina", 14000),
            ("Tapa de Asado", 6500),
            ("Pechito de Cerdo", 5500)
        ]

    def _cargar_demo_completa(self):
        self._cargar_destacados_demo()
        demo_precios = {
            "Cortes Vacunos": [
                ("Asado de Tira", 7500), ("Vacío", 8200), ("Bife de Chorizo", 11000), 
                ("Roast Beef", 6200), ("Tapa de Asado", 6800), ("Paleta", 5900)
            ],
            "Cerdo": [
                ("Pechito", 5500), ("Bondiola", 7200), ("Carré", 6800), 
                ("Costillitas", 6000), ("Matambrito", 8500)
            ],
            "Embutidos": [
                ("Chorizo Puro Cerdo", 4500), ("Morcilla", 3200), 
                ("Salchicha Parrillera", 5100), ("Chinchulín", 2800)
            ]
        }
        self.zona2_precios.set_items(demo_precios)

