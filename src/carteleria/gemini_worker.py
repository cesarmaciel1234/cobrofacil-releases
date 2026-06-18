import os
import json
import time
import threading
import datetime
import sqlite3
import traceback
from src.utils.paths import get_base_path
from src.logger import logger

class GeminiWorker:
    """
    Hilo asíncrono que se despierta 1 vez al día, pide a Gemini 3 a 5 plantillas 
    nuevas y las guarda en lobo.db (plantillas_carteleria) para que la base de datos 
    mute sin gastar cuota extra.
    """
    _instance = None
    _thread = None
    _stop_event = threading.Event()

    @classmethod
    def start_worker(cls):
        if not cls._instance:
            cls._instance = GeminiWorker()
            cls._thread = threading.Thread(target=cls._instance._run_loop, daemon=True)
            cls._thread.start()

    @classmethod
    def stop_worker(cls):
        if cls._instance:
            cls._stop_event.set()

    def __init__(self):
        base_app_path = get_base_path()
        self.db_path = os.path.join(base_app_path, "lobo.db")
        self.config_path = os.path.join(base_app_path, "config.json")
        self.tracker_path = os.path.join(base_app_path, "last_ai_gen.json")

    def _get_api_key(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            return cfg.get("gemini_api_key", "")
        except:
            return ""

    def _ya_se_ejecuto_hoy(self):
        hoy = datetime.datetime.now().strftime("%Y-%m-%d")
        if os.path.exists(self.tracker_path):
            try:
                with open(self.tracker_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("last_run") == hoy:
                        return True
            except:
                pass
        return False

    def _marcar_ejecutado_hoy(self):
        hoy = datetime.datetime.now().strftime("%Y-%m-%d")
        try:
            with open(self.tracker_path, "w", encoding="utf-8") as f:
                json.dump({"last_run": hoy}, f)
        except:
            pass

    def _run_loop(self):
        logger.info("GeminiWorker Diario: Iniciado.")
        # Esperar 30 segundos antes de la primera evaluación para no saturar el inicio
        if self._stop_event.wait(30): return
        
        try:
            from google import genai
            from google.genai import types
            genai_available = True
        except ImportError:
            genai_available = False
        
        while not self._stop_event.is_set():
            if self._ya_se_ejecuto_hoy():
                # Si ya se ejecutó, dormir 1 hora y volver a chequear
                if self._stop_event.wait(3600): break
                continue

            if not genai_available:
                logger.warning("GeminiWorker: pip install google-genai requerido.")
                try:
                    os.system("pip install google-genai")
                    from google import genai
                    from google.genai import types
                    genai_available = True
                except:
                    pass
                if self._stop_event.wait(3600): break
                continue

            api_key = self._get_api_key()
            if not api_key:
                logger.info("GeminiWorker: Sin API Key de Gemini, durmiendo...")
                if self._stop_event.wait(3600): break
                continue

            # Llamada diaria a Gemini
            try:
                client = genai.Client(api_key=api_key)
                self._generar_plantillas(client)
                self._marcar_ejecutado_hoy()
                logger.info("GeminiWorker: Plantillas generadas con éxito por hoy.")
            except Exception as e:
                logger.error(f"GeminiWorker: Error generando plantillas: {e}")
                # Si hay error, intentar en 1 hora
                if self._stop_event.wait(3600): break
                continue

            # Dormir hasta el siguiente chequeo (1 hora)
            if self._stop_event.wait(3600): break

    def _generar_plantillas(self, client):
        prompt = """
        Eres un experto en marketing de carnicerías y fiambrerías. 
        Genera un arreglo JSON con entre 3 y 5 plantillas de mensajes cortos (1-2 oraciones) 
        para una cartelería digital, diseñados para generar un impulso de compra.
        
        El mensaje puede contener estas etiquetas opcionales para ser reemplazadas: {barrio}, {localidad}, {momento_dia}, {dia_semana}.
        
        Estructura requerida para cada plantilla en el JSON:
        - "texto_plantilla": El mensaje corto. (ej. "¡Qué frío en {barrio}! Llevá el mejor osobuco a la {momento_dia}.")
        - "filtro_clima": "frio", "calor", "lluvioso" o "indiferente"
        - "filtro_momento": "mañana", "tarde", "noche" o "indiferente"
        - "filtro_tipo_dia": "semana", "finde" o "indiferente"
        - "categoria_producto": "Guiso/Horno", "Asado", "Minutas", "Cerdo", "Pollo" o "Indiferente"
        
        Varía el tipo de mensajes (algunos para asado el finde, otros para minutas rápidas, etc.).
        Devuelve SOLO el JSON válido, sin formato markdown extra.
        """
        
        # En el SDK nuevo genai, se llama model.generate_content
        from google.genai import types
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        
        texto_respuesta = response.text
        plantillas = json.loads(texto_respuesta)
        
        if isinstance(plantillas, list) and len(plantillas) > 0:
            self._guardar_en_db(plantillas)

    def _guardar_en_db(self, plantillas):
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Asegurarse de que exista la tabla
            c.execute('''
            CREATE TABLE IF NOT EXISTS plantillas_carteleria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                texto_plantilla TEXT,
                filtro_clima TEXT,
                filtro_momento TEXT,
                filtro_tipo_dia TEXT,
                categoria_producto TEXT
            )
            ''')
            
            registros = []
            for p in plantillas:
                registros.append((
                    p.get("texto_plantilla", ""),
                    p.get("filtro_clima", "indiferente"),
                    p.get("filtro_momento", "indiferente"),
                    p.get("filtro_tipo_dia", "indiferente"),
                    p.get("categoria_producto", "Indiferente")
                ))
                
            c.executemany('''
            INSERT INTO plantillas_carteleria (texto_plantilla, filtro_clima, filtro_momento, filtro_tipo_dia, categoria_producto)
            VALUES (?, ?, ?, ?, ?)
            ''', registros)
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error guardando plantillas en DB: {e}")
