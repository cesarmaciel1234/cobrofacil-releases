from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QMessageBox,
)
from PyQt6.QtCore import Qt
from src.utils.qt_compat import qt_exec
from src.config import config


class DialogoCatalogoClientes(QDialog):
    """Misma lógica que Publicidad TV: buscar, tildar, acciones rápidas, generar."""

    def __init__(self, parent=None, preseleccion_ids=None):
        super().__init__(parent)
        self.setWindowTitle("Catálogo para clientes")
        self.setMinimumSize(520, 640)
        self.resize(540, 700)
        self._pre = set(str(x) for x in (preseleccion_ids or []))
        self.setStyleSheet("""
            QDialog { background: #F8FAFC; }
            QLabel { color: #334155; font-size: 13px; }
            QLineEdit {
                padding: 10px 12px; border: 1px solid #CBD5E1; border-radius: 8px;
                background: #FFFFFF; color: #0F172A;
            }
            QListWidget {
                background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px;
                color: #1E293B; font-size: 13px; padding: 6px;
            }
            QListWidget::item { padding: 6px 8px; border-radius: 6px; }
            QListWidget::item:hover { background: #F1F5F9; }
            QPushButton {
                background: #F1F5F9; color: #1E293B; border: 1px solid #CBD5E1;
                border-radius: 8px; padding: 10px 14px; font-weight: 700;
            }
            QPushButton:hover { background: #E2E8F0; }
            QPushButton#primary {
                background: #FACC15; color: #1E293B; border: none;
            }
        """)
        self._armar()
        self._cargar()

    def _armar(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(12)
        info = QLabel(
            "Buscá y tildá los productos, igual que en Publicidad TV. "
            "El PDF usa la <b>foto asociada</b> (PNG de galería) y el precio de venta."
        )
        info.setWordWrap(True)
        lay.addWidget(info)

        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar producto…")
        self.txt_buscar.textChanged.connect(self._filtrar)
        lay.addWidget(self.txt_buscar)

        top = QHBoxLayout()
        btn_ofertas = QPushButton("Marcar ofertas")
        btn_ofertas.clicked.connect(self._marcar_ofertas)
        btn_foto = QPushButton("Marcar con foto")
        btn_foto.clicked.connect(self._marcar_con_foto)
        btn_vis = QPushButton("Tildar visibles")
        btn_vis.clicked.connect(self._marcar_visibles)
        btn_limpiar = QPushButton("Limpiar")
        btn_limpiar.clicked.connect(self._limpiar)
        for b in (btn_ofertas, btn_foto, btn_vis, btn_limpiar):
            top.addWidget(b)
        lay.addLayout(top)

        self.lista = QListWidget()
        lay.addWidget(self.lista, 1)

        self.txt_titulo = QLineEdit("CATÁLOGO")
        self.txt_titulo.setPlaceholderText("Título del PDF")
        self.txt_contacto = QLineEdit("")
        self.txt_contacto.setPlaceholderText("WhatsApp / teléfono (opcional)")
        try:
            phone = str(config.get("phone") or "").strip()
            if phone and phone.lower() != "no disponible":
                self.txt_contacto.setText(phone)
        except Exception:
            pass
        lay.addWidget(self.txt_titulo)
        lay.addWidget(self.txt_contacto)

        btn = QPushButton("Generar PDF y abrir")
        btn.setObjectName("primary")
        btn.clicked.connect(self._generar)
        lay.addWidget(btn)

    def _cargar(self):
        self.lista.clear()
        productos = []
        try:
            from src.services.inventario_service import InventarioService
            productos, _ok = InventarioService.obtener_lista_de_productos("", "", limite=800)
        except Exception:
            try:
                from src.motor_descuentos.cerebro.motor_ofertas import MotorOfertas
                productos = MotorOfertas().buscar_productos("", None, False) or []
            except Exception:
                productos = []
        for row in productos or []:
            try:
                row = dict(row)
            except Exception:
                continue
            nombre = (row.get("nombre") or "").strip()
            if not nombre:
                continue
            pid = str(row.get("id") or "")
            oferta = (
                float(row.get("cant_oferta") or 0) > 0
                or float(row.get("precio_oferta") or 0) > 0
                or float(row.get("precio_oferta_relampago") or 0) > 0
            )
            texto = nombre.upper()
            if oferta:
                texto += "  · oferta"
            item = QListWidgetItem(texto)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            item.setData(Qt.ItemDataRole.UserRole, row)
            item.setData(Qt.ItemDataRole.UserRole + 1, nombre)
            item.setData(Qt.ItemDataRole.UserRole + 2, bool(oferta))
            marcado = pid in self._pre
            item.setCheckState(Qt.CheckState.Checked if marcado else Qt.CheckState.Unchecked)
            self.lista.addItem(item)

    def _filtrar(self, texto):
        q = (texto or "").lower().strip()
        for i in range(self.lista.count()):
            item = self.lista.item(i)
            nombre = str(item.data(Qt.ItemDataRole.UserRole + 1) or "").lower()
            item.setHidden(bool(q) and q not in nombre)

    def _marcar_ofertas(self):
        for i in range(self.lista.count()):
            item = self.lista.item(i)
            if item.isHidden():
                continue
            if item.data(Qt.ItemDataRole.UserRole + 2):
                item.setCheckState(Qt.CheckState.Checked)

    def _marcar_con_foto(self):
        from src.carteleria.motor_carteleria.iconos_tv import png_vitrina_path
        for i in range(self.lista.count()):
            item = self.lista.item(i)
            if item.isHidden():
                continue
            p = item.data(Qt.ItemDataRole.UserRole) or {}
            if png_vitrina_path(p):
                item.setCheckState(Qt.CheckState.Checked)

    def _marcar_visibles(self):
        for i in range(self.lista.count()):
            item = self.lista.item(i)
            if not item.isHidden():
                item.setCheckState(Qt.CheckState.Checked)

    def _limpiar(self):
        for i in range(self.lista.count()):
            self.lista.item(i).setCheckState(Qt.CheckState.Unchecked)

    def _elegidos(self):
        out = []
        for i in range(self.lista.count()):
            item = self.lista.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                p = item.data(Qt.ItemDataRole.UserRole)
                if p:
                    out.append(p)
        return out

    def _generar(self):
        productos = self._elegidos()
        if not productos:
            QMessageBox.information(
                self,
                "Catálogo",
                "Tildá al menos un producto (o usá Marcar ofertas / Marcar con foto).",
            )
            return
        from src.carteleria.motor_carteleria.iconos_tv import png_vitrina_path
        lote = []
        for p in productos:
            lote.append({
                "id": str(p.get("id") or ""),
                "nombre": p.get("nombre"),
                "precio": p.get("precio"),
                "precio_oferta": p.get("precio_oferta"),
                "departamento": p.get("departamento") or "",
                "unidad": p.get("unidad") or "UN",
                "png_path": png_vitrina_path(p) or "",
            })
        lote.sort(key=lambda x: (
            0 if x.get("png_path") else 1,
            str(x.get("departamento") or ""),
            str(x.get("nombre") or ""),
        ))
        negocio = ""
        try:
            negocio = str(config.get("business_name") or "").upper()
        except Exception:
            pass
        try:
            from src.creador_pdf_global.motor_pdf import EtiquetaRenderer, abrir_archivo_pdf
            path = EtiquetaRenderer().generar_pdf_catalogo_inventario(
                lote_productos=lote[:80],
                titulo_folleto=self.txt_titulo.text().strip() or "CATÁLOGO",
                negocio=negocio,
                diseno_tipo="clientes",
                contacto=self.txt_contacto.text().strip(),
                nota="Precios de mostrador. Consultá stock y cortes del día.",
            )
            abrir_archivo_pdf(path)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "PDF", str(e))


def abrir_catalogo_clientes(parent=None, preseleccion_ids=None):
    dlg = DialogoCatalogoClientes(parent, preseleccion_ids=preseleccion_ids)
    qt_exec(dlg)
