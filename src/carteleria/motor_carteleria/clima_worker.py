import json
import logging
import urllib.request

from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger("CarteleriaClima")


class ClimaWorker(QThread):
    clima_actualizado = pyqtSignal(str, str)  # icon_name, text

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        if self.isInterruptionRequested():
            return
        try:
            url = (
                "https://api.open-meteo.com/v1/forecast"
                "?latitude=-34.4587&longitude=-58.9142&current_weather=true"
            )
            req = urllib.request.Request(url, headers={"User-Agent": "CobroFacil-Carteleria"})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
            temp = data.get("current_weather", {}).get("temperature", 22)
            code = data.get("current_weather", {}).get("weathercode", 0)

            icon_name = "sol"
            if code in [1, 2, 3, 45, 48]:
                icon_name = "nube"
            elif code >= 51:
                icon_name = "lluvia"

            if not self.isInterruptionRequested():
                self.clima_actualizado.emit(icon_name, f"{int(temp)}°C Pilar")
        except Exception as exc:
            logger.debug("Clima no disponible: %s", exc)
