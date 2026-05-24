import json
import os
from src.logger import logger

class Config:
    """Handles application settings and business information."""
    
    DEFAULT_CONFIG = {
        "caja_id": 1,
        "business_name": "PUNPRO BUSINESS",
        "currency_symbol": "$",
        "currency_code": "ARS",
        "address": "Calle Falsa 123",
        "phone": "555-0199",
        "footer_message": "Gracias por su compra!",
        "tax_percentage": 0.0,
        "theme": "midnight",
        "balanza_habilitada": True,
        "balanza_prefijo": "20",
        "balanza_modo": "Peso Neto (Kg)",
        "balanza_plu_inicio": 3,
        "balanza_plu_largo": 4, # 4 dígitos de PLU (Dígitos 3,4,5,6)
        "balanza_val_inicio": 8, # El valor empieza en el dígito 8 (Dígitos 8,9,10,11,12)
        "balanza_val_largo": 5,
        "balanza_divisor": 1000,
        "db_path": "",
        "db_name": "punpro.db",
        "server_password": "1234",
        "update_server_ip": "",
        "update_auth_token": "1234",
        "shared_folder_name": "tpv pro 2026",
        "local_pin": "1234"
    }

    _instance = None
    current_user = None  # To store the logged-in user

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        from src.utils.paths import get_base_path
        self.config_path = os.path.join(get_base_path(), "config.json")
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.data = {**self.DEFAULT_CONFIG, **json.load(f)}
                logger.info("Configuration loaded from file.")
            except Exception as e:
                logger.error(f"Error loading config.json: {e}")
                self.data = self.DEFAULT_CONFIG.copy()
        else:
            self.data = self.DEFAULT_CONFIG.copy()
            self.save()
            logger.info("New configuration file created with defaults.")

    def save(self):
        """Saves current configuration to disk."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4)
            logger.info("Configuration saved successfully.")
        except Exception as e:
            logger.error(f"Error saving config.json: {e}")

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()

# Global config instance
config = Config()
