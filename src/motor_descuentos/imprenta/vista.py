from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QMessageBox
from PyQt6.QtCore import Qt

from src.motor_descuentos.compartido.tarjeta_modulo import TarjetaModulo
from src.motor_descuentos.compartido.shell_modulo import barra_modulo, QSS_MODULO


class PaginaImprenta(QWidget):
    """Solo PDF para clientes. No abre el taller de ofertas ni comparte su estado."""

    def __init__(self, on_back, parent=None):
        super().__init__(parent)
        self.setObjectName("ModuloPromoAislado")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(QSS_MODULO)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(barra_modulo("Imprenta / PDF", on_back))
        body = QWidget()
        body.setStyleSheet("background: #F1F5F9;")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(28, 24, 28, 24)
        intro = QLabel(
            "Este módulo solo imprime. Las ofertas se cargan en «Ofertas por producto»; "
            "la TV, en «Publicidad TV»."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("color: #475569; font-size: 13px; background: transparent; border: none;")
        bl.addWidget(intro)
        grid = QGridLayout()
        grid.setSpacing(16)
        cards = (
            ("cat", "📸", "Catálogo clientes", "Elegís productos y se arma el PDF con foto."),
            ("ofe", "🔥", "Folleto de ofertas", "Lee las promos ya guardadas. No las edita."),
            ("lista", "📋", "Lista de precios", "Tabla compacta con miniatura."),
        )
        for i, (cod, ico, tit, sub) in enumerate(cards):
            card = TarjetaModulo(cod, ico, tit, sub)
            card.clicked.connect(lambda c=cod: self._abrir(c))
            grid.addWidget(card, i // 2, i % 2)
        bl.addLayout(grid)
        bl.addStretch()
        root.addWidget(body, 1)

    def _abrir(self, codigo):
        if codigo == "cat":
            from src.ui_global.inventario_ui.moleculas.dialogo_catalogo_clientes import abrir_catalogo_clientes
            abrir_catalogo_clientes(self)
            return
        if codigo == "ofe":
            self._pdf_ofertas()
            return
        self._pdf_lista()

    def _pdf_lista(self):
        from src.services.inventario_service import InventarioService
        from src.carteleria.motor_carteleria.iconos_tv import png_vitrina_path
        rows, _ok = InventarioService.obtener_lista_de_productos("", "", limite=800)
        lote = []
        for p in rows or []:
            lote.append({
                "id": str(p.get("id") or ""),
                "nombre": p.get("nombre"),
                "precio": p.get("precio"),
                "precio_oferta": p.get("precio_oferta"),
                "departamento": p.get("departamento") or "",
                "unidad": p.get("unidad") or "UN",
                "png_path": png_vitrina_path(p) or "",
            })
        lote = lote[:80]
        self._generar(lote, "LISTA DE PRECIOS", "lista", "Precios de mostrador.")

    def _pdf_ofertas(self):
        from src.motor_descuentos.ofertas.motor import MotorOfertas
        from src.carteleria.motor_carteleria.iconos_tv import png_vitrina_path
        rows = MotorOfertas().obtener_productos_en_oferta()
        lote = []
        for p in rows or []:
            lote.append({
                "id": str(p.get("id") or ""),
                "nombre": p.get("nombre"),
                "precio": p.get("precio"),
                "precio_oferta": p.get("precio_oferta"),
                "departamento": p.get("departamento") or "",
                "unidad": p.get("unidad") or "UN",
                "png_path": png_vitrina_path(p) or "",
            })
        self._generar(lote[:48], "OFERTAS", "clientes", "Promociones vigentes. Solo lectura desde Imprenta.")

    def _generar(self, lote, titulo, diseno, nota):
        if not lote:
            QMessageBox.warning(self, "Aviso", "No hay productos para armar el PDF.")
            return
        negocio, contacto = "", ""
        try:
            from src.config import config as _cfg
            negocio = str(_cfg.get("business_name") or "").upper()
            phone = str(_cfg.get("phone") or "").strip()
            if phone and phone.lower() != "no disponible":
                contacto = phone
        except Exception:
            pass
        try:
            from src.creador_pdf_global.motor_pdf import EtiquetaRenderer, abrir_archivo_pdf
            path = EtiquetaRenderer().generar_pdf_catalogo_inventario(
                lote_productos=lote,
                titulo_folleto=titulo,
                negocio=negocio,
                diseno_tipo=diseno,
                contacto=contacto,
                nota=nota,
            )
            abrir_archivo_pdf(path)
        except Exception as e:
            QMessageBox.critical(self, "PDF", str(e))
