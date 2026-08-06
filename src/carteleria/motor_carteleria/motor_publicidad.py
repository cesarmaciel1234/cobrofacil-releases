import os
import json
import random
from src.utils.paths import get_base_path

class MotorPublicidad:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MotorPublicidad, cls).__new__(cls)
            cls._instance.config_path = os.path.join(get_base_path(), "publicidad_config.json")
            cls._instance._promocionados_cache = []
            cls._instance.cargar_configuracion()
        return cls._instance

    def cargar_configuracion(self):
        """Carga la lista de nombres o códigos de productos promocionados."""
        self._promocionados_cache = []
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._promocionados_cache = [str(item).lower().strip() for item in data.get("promocionados", [])]
            except Exception:
                pass

    def guardar_configuracion(self, lista_nombres):
        """Guarda la lista de nombres de productos promocionados."""
        data = {"promocionados": [str(item).strip() for item in lista_nombres]}
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            self.cargar_configuracion()
        except Exception:
            pass

    def is_promocionado(self, nombre_producto):
        """Devuelve True si el producto debe mostrarse como Anuncio (TarjetaPublicidad)."""
        if not nombre_producto:
            return False
        nombre_lower = str(nombre_producto).lower().strip()
        # Verificamos si hay coincidencia exacta o si contiene el nombre
        for promo in self._promocionados_cache:
            if promo and promo in nombre_lower:
                return True
        return False
        
    def inyectar_en_top10(self, lista_top10):
        """
        Recibe la lista actual del 'Recomendado' (Clavos) de la DB.
        Verifica si alguno de los promocionados no está en la lista y lo inyecta artificialmente,
        o simplemente marca el índice del producto promocionado si ya estaba.
        Retorna: (nueva_lista, indice_promocionado)
        """
        self.cargar_configuracion() # Forzar recarga por si el TPV lo modificó
        if not self._promocionados_cache or not lista_top10:
            return lista_top10, -1
            
        lista_segura = list(lista_top10)
            
        # 1. Buscamos si algún producto del top10 ya es promocionado
        for i, prod in enumerate(lista_segura):
            nombre = str(prod[0] if isinstance(prod, tuple) else prod.get("nombre", ""))
            if self.is_promocionado(nombre):
                return lista_segura, i
                
        # 2. Si no hay ninguno, forzamos la inyección del primero en la posición 1 (segundo ítem)
        if len(lista_segura) > 1 and len(self._promocionados_cache) > 0:
            # Reemplazamos la tupla con una que tenga el nombre del promocionado,
            # y rellenamos los demás campos (precio, precio_oferta, regla, categoria, stock) con vacíos/0 
            # para evitar IndexErrors en carrusel_destacados si espera más campos.
            lista_segura[1] = (self._promocionados_cache[0].upper(), 0.0, 0.0, "", "", 0.0)
            return lista_segura, 1
            
        return lista_segura, -1

# Instancia global (Singleton)
motor_publicidad = MotorPublicidad()
