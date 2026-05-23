"""
admin15_actualizaciones.py
Panel de Actualizaciones — TPV Pro 2026
========================================
Vista para el ADMINISTRADOR:
  • Publicar nuevas versiones (generar manifest + marcar módulos como beta/estable)
  • Ver qué PCs están conectadas y en qué versión están
  • Forzar actualización de un módulo específico

Vista para el CLIENTE (PC en sucursal):
  • Verificar si hay actualizaciones disponibles
  • Elegir canal: Estable o Beta
  • Ver changelog de qué cambió
  • Aplicar actualizaciones con un clic
"""
import os
import json
import socket
import threading
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QMessageBox, QComboBox, QProgressBar, QTextEdit,
    QCheckBox, QLineEdit, QSplitter, QGroupBox, QGraphicsDropShadowEffect,
    QApplication
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QFont, QBrush

UPDATE_PORT = 38001
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VERSION_FILE = os.path.join(BASE_DIR, "version.json")


# ── Worker thread para operaciones de red (no bloquear UI) ───────────────────
class UpdateWorker(QThread):
    progreso = pyqtSignal(int, str)
    terminado = pyqtSignal(object)  # ResultadoActualizacion

    def __init__(self, server_ip="", canal="stable", solo_modulos=None, dry_run=False):
        super().__init__()
        self.server_ip    = server_ip
        self.canal        = canal
        self.solo_modulos = solo_modulos
        self.dry_run      = dry_run

    def run(self):
        from src.updater.update_client import verificar_actualizaciones
        res = verificar_actualizaciones(
            server_ip=self.server_ip,
            canal_filtro=self.canal,
            solo_modulos=self.solo_modulos,
            dry_run=self.dry_run,
            callback_progreso=lambda p, m: self.progreso.emit(p, m)
        )
        self.terminado.emit(res)


class PublishWorker(QThread):
    terminado = pyqtSignal(str)

    def __init__(self, canal):
        super().__init__()
        self.canal = canal

    def run(self):
        try:
            from src.updater.update_server import generar_manifest
            manifest = generar_manifest(self.canal)
            n = len(manifest.get("modules", {}))
            self.terminado.emit(f"✅ Manifest publicado: {n} módulos — canal {self.canal.upper()}")
        except Exception as e:
            self.terminado.emit(f"❌ Error: {e}")


# ════════════════════════════════════════════════════════════════════════════
class Admin15Actualizaciones(QWidget):
    from PyQt5.QtCore import pyqtSignal as _ps
    request_dashboard = _ps()

    def __init__(self):
        super().__init__()
        self.worker = None
        self._es_servidor = self._detectar_si_es_servidor()
        self.setup_ui()
        self._refrescar_info_local()

    def _detectar_si_es_servidor(self) -> bool:
        """Si el port 38001 se puede abrir localmente, o si ya responde localmente, somos el servidor."""
        try:
            s = socket.socket()
            s.bind(("0.0.0.0", UPDATE_PORT))
            s.close()
            return True
        except:
            pass
            
        try:
            from src.updater.update_client import ping_servidor
            if ping_servidor("127.0.0.1"):
                return True
        except:
            pass
            
        return False


    # ── UI ──────────────────────────────────────────────────────────────────
    def setup_ui(self):
        self.setStyleSheet("background:#F1F5F9; font-family:'Segoe UI';")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        # Header
        hdr = QFrame()
        hdr.setStyleSheet("background:#0f172a; color:white;")
        hdr.setFixedHeight(68)
        hhl = QHBoxLayout(hdr)
        hhl.setContentsMargins(18, 0, 18, 0)

        btn_volver = QPushButton("🔙 Volver")
        btn_volver.setStyleSheet(
            "background:rgba(255,255,255,0.15); color:white; font-weight:bold;"
            "border:1px solid rgba(255,255,255,0.3); border-radius:6px; padding:7px 14px;")
        btn_volver.clicked.connect(self.request_dashboard.emit)
        hhl.addWidget(btn_volver)
        hhl.addSpacing(18)

        lbl = QLabel("🔄  Sistema de Actualizaciones por Red — TPV Pro 2026")
        lbl.setStyleSheet("font-size:19px; font-weight:800;")
        hhl.addWidget(lbl)
        hhl.addStretch()

        # Badge servidor/cliente
        modo = "🖥️  SERVIDOR MAESTRO" if self._es_servidor else "💻  PC CLIENTE"
        color_badge = "#10b981" if self._es_servidor else "#3b82f6"
        badge = QLabel(modo)
        badge.setStyleSheet(
            f"background:{color_badge}; color:white; font-weight:bold; font-size:13px;"
            f"padding:6px 16px; border-radius:20px;")
        hhl.addWidget(badge)

        root.addWidget(hdr)

        body = QVBoxLayout()
        body.setContentsMargins(20, 16, 20, 16)
        body.setSpacing(14)

        # Panel de versión actual
        info_frame = QFrame()
        info_frame.setStyleSheet(
            "QFrame{background:white; border:1px solid #e2e8f0; border-radius:10px; padding:14px;}")
        ifl = QHBoxLayout(info_frame)

        self.lbl_version_local = QLabel("📦 Versión local: cargando...")
        self.lbl_version_local.setStyleSheet("font-size:15px; font-weight:bold; color:#1e293b;")
        ifl.addWidget(self.lbl_version_local)

        self.lbl_server_ip = QLabel()
        self.lbl_server_ip.setStyleSheet("font-size:13px; color:#64748b;")
        ifl.addWidget(self.lbl_server_ip)
        ifl.addStretch()

        self.lbl_ultima_actualizacion = QLabel("Última actualización: —")
        self.lbl_ultima_actualizacion.setStyleSheet("font-size:12px; color:#94a3b8;")
        ifl.addWidget(self.lbl_ultima_actualizacion)

        body.addWidget(info_frame)

        # ── Si es SERVIDOR: Panel de Publicación ──
        if self._es_servidor:
            body.addWidget(self._crear_panel_servidor())
        
        # ── Panel de actualización (cliente o servidor verificando) ──
        body.addWidget(self._crear_panel_cliente())

        # Log / tabla de módulos
        body.addWidget(self._crear_tabla_modulos(), stretch=1)

        root.addLayout(body)

    def _crear_panel_servidor(self) -> QFrame:
        grp = QGroupBox("🖥️  Control de Servidor — Publicar Actualizaciones")
        grp.setStyleSheet(
            "QGroupBox{background:white; border:2px solid #10b981; border-radius:10px;"
            "font-size:14px; font-weight:bold; color:#065f46; padding:10px; margin-top:8px;}"
            "QGroupBox::title{subcontrol-origin:margin; left:10px; padding:0 6px;}")
        gl = QVBoxLayout(grp)
        gl.setSpacing(10)

        # Canal y versión
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Canal a publicar:"))
        self.cmb_canal_pub = QComboBox()
        self.cmb_canal_pub.addItems(["stable", "beta"])
        self.cmb_canal_pub.setStyleSheet("padding:7px; border:1px solid #CBD5E1; border-radius:5px; background:white;")
        row1.addWidget(self.cmb_canal_pub)

        row1.addWidget(QLabel("Nueva versión app:"))
        self.txt_nueva_version = QLineEdit()
        self.txt_nueva_version.setPlaceholderText("ej: 2026.2.0")
        self.txt_nueva_version.setStyleSheet("padding:7px; border:1px solid #CBD5E1; border-radius:5px; background:white; min-width:120px;")
        row1.addWidget(self.txt_nueva_version)
        row1.addStretch()

        btn_pub = QPushButton("🚀 Publicar Actualización")
        btn_pub.setStyleSheet(
            "background:#10b981; color:white; font-weight:bold; padding:10px 24px;"
            "border-radius:7px; font-size:14px;")
        btn_pub.clicked.connect(self._publicar)
        row1.addWidget(btn_pub)
        gl.addLayout(row1)

        # Marcar módulo como beta
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Marcar módulo como BETA (prueba selectiva):"))
        self.txt_modulo_beta = QLineEdit()
        self.txt_modulo_beta.setPlaceholderText("ej: src/cajero/paso5_terminal.py")
        self.txt_modulo_beta.setStyleSheet("padding:7px; border:1px solid #CBD5E1; border-radius:5px; background:white;")
        row2.addWidget(self.txt_modulo_beta, stretch=1)
        btn_beta = QPushButton("🧪 Marcar Beta")
        btn_beta.setStyleSheet("background:#7c3aed; color:white; font-weight:bold; padding:9px 18px; border-radius:6px;")
        btn_beta.clicked.connect(self._marcar_beta)
        row2.addWidget(btn_beta)
        btn_estable = QPushButton("✅ Promover a Estable")
        btn_estable.setStyleSheet("background:#0284c7; color:white; font-weight:bold; padding:9px 18px; border-radius:6px;")
        btn_estable.clicked.connect(self._promover_estable)
        row2.addWidget(btn_estable)
        gl.addLayout(row2)

        # ── TARJETA GRANDE DE IP — visible de un vistazo, sin buscar nada ──
        mi_ip = self._get_mi_ip()
        self._mi_ip_actual = mi_ip

        ip_card = QFrame()
        ip_card.setStyleSheet(
            "QFrame{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #0f172a,stop:1 #1e3a5f);border-radius:12px;}")
        ip_lay = QHBoxLayout(ip_card)
        ip_lay.setContentsMargins(20, 14, 20, 14)
        ip_lay.setSpacing(18)

        ico_lbl = QLabel("\U0001f310")
        ico_lbl.setStyleSheet("font-size:36px;background:transparent;border:none;")
        ip_lay.addWidget(ico_lbl)

        txt_lay = QVBoxLayout()
        lbl_inst = QLabel("ESCRIBI ESTA IP EN LAS PCs DEL LOCAL")
        lbl_inst.setStyleSheet(
            "color:rgba(255,255,255,0.55);font-size:11px;font-weight:900;"
            "letter-spacing:2px;background:transparent;border:none;")
        txt_lay.addWidget(lbl_inst)

        self.lbl_ip_grande = QLabel(f"{mi_ip}   :   {UPDATE_PORT}")
        self.lbl_ip_grande.setStyleSheet(
            "color:#34d399;font-size:32px;font-weight:900;"
            "font-family:'Consolas','Lucida Console',monospace;"
            "letter-spacing:3px;background:transparent;border:none;")
        txt_lay.addWidget(self.lbl_ip_grande)

        lbl_sub2 = QLabel("IP del Servidor Maestro  (puerto del actualizador)")
        lbl_sub2.setStyleSheet(
            "color:rgba(255,255,255,0.4);font-size:11px;"
            "background:transparent;border:none;")
        txt_lay.addWidget(lbl_sub2)
        ip_lay.addLayout(txt_lay)
        ip_lay.addStretch()

        btn_copiar = QPushButton("\U0001f4cb  COPIAR IP")
        btn_copiar.setStyleSheet(
            "QPushButton{background:#34d399;color:#0f172a;font-weight:900;"
            "font-size:14px;padding:12px 22px;border-radius:8px;border:none;}"
            "QPushButton:hover{background:#6ee7b7;}"
            "QPushButton:pressed{background:#10b981;}")
        btn_copiar.clicked.connect(self._copiar_ip)
        ip_lay.addWidget(btn_copiar)

        btn_solo = QPushButton("\U0001f4cb  Solo IP")
        btn_solo.setStyleSheet(
            "QPushButton{background:rgba(255,255,255,0.12);color:white;"
            "font-weight:bold;padding:12px 16px;border-radius:8px;"
            "border:1px solid rgba(255,255,255,0.2);}"
            "QPushButton:hover{background:rgba(255,255,255,0.2);}")
        btn_solo.clicked.connect(lambda checked=False, ip=mi_ip: self._copiar_texto(ip))
        ip_lay.addWidget(btn_solo)

        gl.addWidget(ip_card)
        return grp

    def _copiar_ip(self):
        mi_ip = self._get_mi_ip()
        QApplication.clipboard().setText(mi_ip)
        orig = self.lbl_ip_grande.text()
        self.lbl_ip_grande.setText("\u2705  iIP copiada al portapapeles!")
        QTimer.singleShot(2000, lambda: self.lbl_ip_grande.setText(orig))

    def _copiar_texto(self, texto: str):
        QApplication.clipboard().setText(texto)

    def _crear_panel_cliente(self) -> QFrame:
        grp = QGroupBox("💻  Verificar y Aplicar Actualizaciones")
        grp.setStyleSheet(
            "QGroupBox{background:white; border:2px solid #3b82f6; border-radius:10px;"
            "font-size:14px; font-weight:bold; color:#1e40af; padding:10px; margin-top:8px;}"
            "QGroupBox::title{subcontrol-origin:margin; left:10px; padding:0 6px;}")
        gl = QVBoxLayout(grp)

        row = QHBoxLayout()
        row.addWidget(QLabel("IP del servidor:"))
        self.txt_server_ip = QLineEdit()
        self.txt_server_ip.setPlaceholderText("192.168.1.100  (vacío = auto-detectar)")
        self.txt_server_ip.setStyleSheet("padding:7px; border:1px solid #CBD5E1; border-radius:5px; background:white; min-width:200px;")
        row.addWidget(self.txt_server_ip)

        row.addWidget(QLabel("Canal:"))
        self.cmb_canal = QComboBox()
        self.cmb_canal.addItems(["stable", "beta"])
        self.cmb_canal.setStyleSheet("padding:7px; border:1px solid #CBD5E1; border-radius:5px; background:white;")
        row.addWidget(self.cmb_canal)

        row.addWidget(QLabel("Solo módulo:"))
        self.txt_solo_modulo = QLineEdit()
        self.txt_solo_modulo.setPlaceholderText("ej: src/cajero/paso5_terminal.py  (vacío = todos)")
        self.txt_solo_modulo.setStyleSheet("padding:7px; border:1px solid #CBD5E1; border-radius:5px; background:white;")
        row.addWidget(self.txt_solo_modulo, stretch=1)

        btn_check = QPushButton("🔍 Verificar")
        btn_check.setStyleSheet("background:#64748b; color:white; font-weight:bold; padding:9px 18px; border-radius:6px;")
        btn_check.clicked.connect(self._verificar_dry_run)
        row.addWidget(btn_check)

        btn_aplicar = QPushButton("⬇️  Aplicar Actualización")
        btn_aplicar.setStyleSheet("background:#2563eb; color:white; font-weight:bold; padding:9px 22px; border-radius:6px; font-size:14px;")
        btn_aplicar.clicked.connect(self._aplicar_actualizacion)
        row.addWidget(btn_aplicar)

        gl.addLayout(row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(
            "QProgressBar{border:1px solid #CBD5E1; border-radius:6px; height:20px; background:#F1F5F9;}"
            "QProgressBar::chunk{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #2563eb, stop:1 #7c3aed); border-radius:6px;}")
        self.progress_bar.hide()
        gl.addWidget(self.progress_bar)

        self.lbl_progreso = QLabel("")
        self.lbl_progreso.setStyleSheet("color:#475569; font-size:12px;")
        gl.addWidget(self.lbl_progreso)

        return grp

    def _crear_tabla_modulos(self) -> QFrame:
        frm = QFrame()
        frm.setStyleSheet("QFrame{background:white; border:1px solid #e2e8f0; border-radius:10px;}")
        fl = QVBoxLayout(frm)
        fl.setContentsMargins(12, 10, 12, 10)

        lbl = QLabel("📋  Módulos del Sistema")
        lbl.setStyleSheet("font-size:14px; font-weight:bold; color:#1e293b;")
        fl.addWidget(lbl)

        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(["Módulo", "Versión", "Canal", "Checksum", "Estado"])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for c in [1, 2, 3, 4]:
            self.tabla.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeToContents)
        self.tabla.setStyleSheet(
            "QTableWidget{background:white; font-size:12px; border:none;}"
            "QHeaderView::section{background:#0f172a; color:white; font-weight:bold; padding:6px; border:none;}")
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        fl.addWidget(self.tabla)

        return frm

    # ── Lógica ───────────────────────────────────────────────────────────────
    def _refrescar_info_local(self):
        if os.path.exists(VERSION_FILE):
            try:
                with open(VERSION_FILE) as f:
                    m = json.load(f)
                version = m.get("app_version", "?")
                build   = m.get("build_date", "")
                self.lbl_version_local.setText(f"📦 Versión local: {version}")
                self.lbl_ultima_actualizacion.setText(f"Generado: {build}")
                self._poblar_tabla(m)
            except:
                pass
        
        mi_ip = self._get_mi_ip()
        if self._es_servidor:
            self.lbl_server_ip.setText(f"🌐 IP servidor: {mi_ip}:{UPDATE_PORT}")
        else:
            self.lbl_server_ip.setText(f"🌐 Tu IP: {mi_ip}")

    def _poblar_tabla(self, manifest: dict):
        mods = manifest.get("modules", {})
        self.tabla.setRowCount(0)
        for rel_path, info in sorted(mods.items()):
            r = self.tabla.rowCount()
            self.tabla.insertRow(r)
            self.tabla.setItem(r, 0, QTableWidgetItem(rel_path))
            self.tabla.setItem(r, 1, QTableWidgetItem(info.get("version", "")))
            
            canal = info.get("channel", "stable")
            item_canal = QTableWidgetItem(canal.upper())
            if canal == "beta":
                item_canal.setForeground(QColor("#7c3aed"))
                item_canal.setFont(QFont("Segoe UI", 9, QFont.Bold))
            else:
                item_canal.setForeground(QColor("#059669"))
            self.tabla.setItem(r, 2, item_canal)
            
            chk = info.get("checksum", "")[:12] + "..."
            self.tabla.setItem(r, 3, QTableWidgetItem(chk))
            self.tabla.setItem(r, 4, QTableWidgetItem("✅ OK"))

    def _publicar(self):
        canal = self.cmb_canal_pub.currentText()
        nueva_ver = self.txt_nueva_version.text().strip()
        
        # Actualizar versión en el manifest si se especificó
        if nueva_ver and os.path.exists(VERSION_FILE):
            try:
                with open(VERSION_FILE) as f:
                    m = json.load(f)
                m["app_version"] = nueva_ver
                with open(VERSION_FILE, "w") as f:
                    json.dump(m, f, indent=2)
            except:
                pass
        
        self.lbl_progreso.setText("Generando manifest...")
        self.worker = PublishWorker(canal)
        self.worker.terminado.connect(self._on_publicado)
        self.worker.start()

    def _on_publicado(self, msg: str):
        self.lbl_progreso.setText(msg)
        self._refrescar_info_local()
        QMessageBox.information(self, "Publicado", msg)

    def _marcar_beta(self):
        modulo = self.txt_modulo_beta.text().strip()
        if not modulo:
            QMessageBox.warning(self, "Error", "Ingresá la ruta del módulo.")
            return
        self._cambiar_canal_modulo(modulo, "beta")

    def _promover_estable(self):
        modulo = self.txt_modulo_beta.text().strip()
        if not modulo:
            QMessageBox.warning(self, "Error", "Ingresá la ruta del módulo.")
            return
        self._cambiar_canal_modulo(modulo, "stable")

    def _cambiar_canal_modulo(self, rel_path: str, canal: str):
        if not os.path.exists(VERSION_FILE):
            return
        try:
            with open(VERSION_FILE) as f:
                m = json.load(f)
            if rel_path in m.get("modules", {}):
                m["modules"][rel_path]["channel"] = canal
                with open(VERSION_FILE, "w") as f:
                    json.dump(m, f, indent=2)
                self._refrescar_info_local()
                QMessageBox.information(self, "✅ Listo",
                    f"Módulo marcado como {canal.upper()}:\n{rel_path}\n\n"
                    "Hacé clic en 'Publicar Actualización' para que los clientes lo vean.")
            else:
                QMessageBox.warning(self, "No encontrado",
                    f"El módulo '{rel_path}' no está en el manifest.\n"
                    "Publicá el manifest primero.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _verificar_dry_run(self):
        self._lanzar_worker(dry_run=True)

    def _aplicar_actualizacion(self):
        self._lanzar_worker(dry_run=False)

    def _lanzar_worker(self, dry_run: bool):
        if self.worker and self.worker.isRunning():
            return
        
        server_ip   = self.txt_server_ip.text().strip().replace(" ", "")
        canal       = self.cmb_canal.currentText()
        solo_mod    = self.txt_solo_modulo.text().strip()
        solo_lista  = [solo_mod] if solo_mod else None
        
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.lbl_progreso.setText("Iniciando...")
        
        self.worker = UpdateWorker(
            server_ip=server_ip,
            canal=canal,
            solo_modulos=solo_lista,
            dry_run=dry_run
        )
        self.worker.progreso.connect(self._on_progreso)
        self.worker.terminado.connect(lambda r: self._on_terminado(r, dry_run))
        self.worker.start()

    def _on_progreso(self, pct: int, msg: str):
        self.progress_bar.setValue(pct)
        self.lbl_progreso.setText(msg)

    def _on_terminado(self, resultado, dry_run: bool):
        self.progress_bar.setValue(100)
        
        if resultado.errores and not resultado.actualizados:
            self.lbl_progreso.setText(f"❌ {resultado.errores[0]}")
            QMessageBox.warning(self, "Sin conexión", resultado.errores[0])
            return
        
        if dry_run:
            if resultado.hay_cambios:
                mods = "\n".join(f"  • {m}" for m in resultado.actualizados)
                QMessageBox.information(self, "🔍 Actualizaciones disponibles",
                    f"Se encontraron {len(resultado.actualizados)} módulo(s) para actualizar"
                    f" (canal {resultado.canal.upper()}):\n\n{mods}\n\n"
                    "Hacé clic en 'Aplicar Actualización' para instalarlas.")
                self.lbl_progreso.setText(f"ℹ️ {len(resultado.actualizados)} actualizaciones disponibles.")
            else:
                QMessageBox.information(self, "✅ Al día",
                    "Todos los módulos están en la última versión.")
                self.lbl_progreso.setText("✅ Ya estás en la última versión.")
        else:
            if resultado.hay_cambios:
                mods = "\n".join(f"  • {m}" for m in resultado.actualizados)
                msg = (f"✅ {len(resultado.actualizados)} módulo(s) actualizados:\n\n{mods}")
                if resultado.necesita_reinicio:
                    msg += "\n\n⚠️ Es necesario REINICIAR el programa para aplicar los cambios del núcleo del sistema."
                if resultado.errores:
                    msg += f"\n\n⚠️ Errores menores:\n" + "\n".join(resultado.errores)
                QMessageBox.information(self, "Actualización completada", msg)
                self.lbl_progreso.setText(f"✅ {len(resultado.actualizados)} módulos actualizados.")
                self._refrescar_info_local()
                
                if resultado.necesita_reinicio:
                    ret = QMessageBox.question(self, "Reiniciar",
                        "¿Reiniciar el programa ahora para aplicar todos los cambios?",
                        QMessageBox.Yes | QMessageBox.No)
                    if ret == QMessageBox.Yes:
                        import sys
                        from PyQt5.QtWidgets import QApplication
                        QApplication.exit(99)  # Código 99 = reinicio
            else:
                QMessageBox.information(self, "✅ Sin cambios",
                    "No hay actualizaciones pendientes.")
                self.lbl_progreso.setText("✅ Ya estás en la última versión.")

    def _get_mi_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
