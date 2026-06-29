import os
from PyQt6.QtWidgets import QApplication
from src.logger import logger

def aplicar_tema(app: QApplication, qss_file: str = "estilo_noche.qss") -> bool:
    """
    Carga y aplica el archivo QSS a la instancia de QApplication.
    
    Args:
        app: Instancia de QApplication
        qss_file: Nombre del archivo qss dentro de src/ui_components
    
    Returns:
        bool: True si el estilo se aplicó correctamente, False de lo contrario.
    """
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        qss_path = os.path.join(current_dir, qss_file)
        
        if not os.path.exists(qss_path):
            logger.error(f"No se encontró el archivo de estilos: {qss_path}")
            return False
            
        with open(qss_path, "r", encoding="utf-8") as f:
            estilo = f.read()
            
        # Opcional: Reemplazar rutas relativas de assets si usamos imágenes en el QSS
        # base_dir = os.path.dirname(os.path.dirname(current_dir))
        # assets_dir = os.path.join(base_dir, "assets").replace("\\", "/")
        # estilo = estilo.replace("url(assets/", f"url({assets_dir}/")
        
        app.setStyleSheet(estilo)
        logger.info(f"Tema cargado correctamente desde {qss_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error aplicando el tema: {e}")
        return False
