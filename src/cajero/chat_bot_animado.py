from src.utils.qt_compat import qt_exec
import os
import sys
import json
import unicodedata
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QPushButton, QLabel
from PyQt6.QtCore import Qt, QTimer, QUrl, pyqtSignal
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtNetwork import QUdpSocket, QHostAddress
from src.utils.qt_compat import connect_webengine_console, webengine_page_transparent

_DIR = os.path.dirname(os.path.abspath(__file__))
MANUAL_JSON = os.path.join(_DIR, "manual_cajero.json")

PASOS_TUTOR = [
    {"msg": "👋 ¡Hola! Soy tu asistente de CobroFacil POS. Estoy aquí para ayudarte.", "espera": 3},
    {"msg": "🛒 TERMINAL DE VENTAS: Simplemente pasa el código de barras del producto con el lector láser.", "espera": 4},
    {"msg": "✏️ Multiplicador: escribe CANTIDAD * CÓDIGO  (Ej: 6*779001234) y presiona ENTER.", "espera": 4},
    {"msg": "➕ Artículo sin código: escribe +PRECIO  (Ej: +500) y presiona ENTER.", "espera": 4},
    {"msg": "⚖️ BALANZA: escanea el código de la balanza (Systel/Kretz). El sistema calcula el precio automáticamente.", "espera": 4},
    {"msg": "💳 COBRAR: presiona F12 (o ENTER con el buscador vacío) para ir a la pantalla de cobro.", "espera": 4},
    {"msg": "💰 Selecciona el método de pago con las flechas ←→: Efectivo, Tarjeta o Mixto. Luego ENTER.", "espera": 4},
    {"msg": "🖨️ FINALIZAR: F1 = cobra e imprime ticket · F2 = cobra sin ticket · ENTER = igual que F2.", "espera": 4},
    {"msg": "🏷️ DESCUENTOS/RECARGOS: F3 = descuento · F4 = recargo (desde la pantalla de cobro).", "espera": 4},
    {"msg": "🚨 CAJÓN ABIERTO: si el borde parpadea en rojo, cierra el cajón físicamente. Se desbloqueará solo.", "espera": 4},
    {"msg": "👮 SUPERVISOR (F11): si necesitás ayuda, presioná F11 y llamá al supervisor.", "espera": 4},
    {"msg": "📋 HISTORIAL (F3): presioná F3 desde el terminal para ver las ventas del día.", "espera": 4},
    {"msg": "🏁 CIERRE DE TURNO (F4): contá el efectivo, ingresá el total y el sistema cerrará tu sesión.", "espera": 4},
    {"msg": "⌨️ RESUMEN DE TECLAS:\nF1=Buscar · F3=Historial · F4=Cierre · F5=Retiro · F6=Ingreso · F7=Balanza · F8=Bloquear · F10=Chatbot · F12=Cobrar", "espera": 5},
    {"msg": "✅ ¡Tutorial completo! Ahora podés consultarme cualquier duda escribiendo en el chat. 💬", "espera": 3},
]

def _normalizar(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto.lower())
    sin_tildes = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"[^\w\s]", "", sin_tildes).strip()

class ChatManual:
    def __init__(self):
        self.entradas = []
        try:
            with open(MANUAL_JSON, "r", encoding="utf-8") as f:
                self.entradas = json.load(f).get("entradas", [])
        except Exception as e:
            self.entradas = [{"id": "error", "preguntas": [], "respuesta": f"⚠️ Error cargando manual: {e}"}]

    def consultar(self, texto: str) -> str:
        q = _normalizar(texto.strip())
        if not q:
            return ""
        mejor_score, mejor_resp = 0, None
        for entrada in self.entradas:
            if not entrada.get("preguntas"):
                continue
            score = sum(len(kw) for kw in entrada["preguntas"] if _normalizar(kw) in q)
            if score > mejor_score:
                mejor_score, mejor_resp = score, entrada["respuesta"]
        if mejor_resp:
            return mejor_resp
        for entrada in self.entradas:
            if entrada.get("id") == "no_encontrado":
                return entrada["respuesta"]
        return "🤔 No encontré información. Consultá con tu supervisor."

HTML_CHAT = r"""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
    html, body {
        height: 100%; margin: 0; padding: 0;
        overflow: hidden;
        background: transparent;
        font-family: 'Segoe UI', -apple-system, sans-serif;
        user-select: none;
    }
    .app-container {
        position: relative; width: 100%; height: 100%;
        display: flex; align-items: flex-end; justify-content: flex-end;
        padding-right: 20px; padding-bottom: 20px; box-sizing: border-box;
    }

    /* ── Robot ── */
    .robot-head {
        position: relative; width: 90px; height: 90px;
        background: url('data:image/svg+xml;utf8,<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><path d="M 16,50 A 20,20 0 0,1 50,30 A 20,20 0 0,1 84,50 C 92,68 80,88 50,88 C 20,88 8,68 16,50 Z" fill="%23161616" stroke="%23888888" stroke-width="6" stroke-linejoin="round"/></svg>') no-repeat center/contain;
        display: flex; align-items: center; justify-content: center;
        cursor: pointer;
        filter: drop-shadow(0 8px 16px rgba(15,23,42,0.45));
        transition: transform 0.3s cubic-bezier(0.175,0.885,0.32,1.275), filter 0.3s ease;
        animation: floatBot 4s ease-in-out infinite;
        z-index: 10;
    }
    .robot-head:hover {
        filter: drop-shadow(0 12px 24px rgba(15,23,42,0.5)) drop-shadow(0 0 8px rgba(56,189,248,0.45));
        transform: scale(1.08) translateY(-4px);
    }
    .robot-head:active { transform: scale(0.92,1.08) translateY(2px); }
    @keyframes floatBot {
        0%,100% { transform: translateY(0px) rotate(0deg); }
        50%      { transform: translateY(-8px) rotate(1.5deg); }
    }

    /* Antena */
    .antenna { position:absolute; top:-14px; display:flex; flex-direction:column; align-items:center; pointer-events:none; }
    .antenna-shaft { width:4px; height:12px; background:#38BDF8; border:2px solid #0F172A; border-bottom:none; }
    .antenna-ball {
        width:10px; height:10px; background:#38BDF8; border:2px solid #0F172A;
        border-radius:50%; box-shadow:0 0 10px #38BDF8;
        animation: pulseLed 1.5s infinite alternate ease-in-out;
    }
    @keyframes pulseLed {
        from { background:#38BDF8; box-shadow:0 0 6px #38BDF8; }
        to   { background:#F43F5E; box-shadow:0 0 14px #F43F5E; }
    }

    /* Órbita */
    .orbit-ring {
        position:absolute; top:-8px; left:-8px; width:102px; height:102px;
        border:2px dashed rgba(56,189,248,0.4); border-radius:50%;
        animation: rotateOrbit 15s linear infinite; pointer-events:none;
        transition: border-color 0.3s ease;
    }
    .robot-head:hover .orbit-ring { border-color:rgba(56,189,248,0.8); animation-duration:8s; }
    @keyframes rotateOrbit { from{transform:rotate(0deg);} to{transform:rotate(360deg);} }

    /* Rubor */
    .blush { position:absolute; width:10px; height:6px; background:#F43F5E; border-radius:50%; filter:blur(1px); opacity:0.15; bottom:26px; transition:opacity 0.3s ease; }
    .blush-left { left:14px; } .blush-right { right:14px; }
    .robot-head:hover .blush { opacity:0.7; }

    /* Ojos */
    .eyes-container { display:flex; gap:12px; margin-top:32px; z-index:2; }
    .eye { position:relative; width:18px; height:18px; background:#000; border:3px solid #888; border-radius:50%; display:flex; align-items:center; justify-content:center; }
    .eye-pupil { position:absolute; width:6px; height:10px; background:#38BDF8; border-radius:2px; box-shadow:0 0 8px #38BDF8; transition:opacity 0.18s ease,transform 0.18s ease; }
    .eye.blinking { animation: normalBlink 0.15s ease-in-out; }
    @keyframes normalBlink { 0%,100%{transform:scaleY(1);} 50%{transform:scaleY(0.05);} }
    .eye-wink-shape { position:absolute; top:2px; left:-1px; width:18px; height:10px; border-top:4px solid #38BDF8; border-radius:50% 50% 0 0; box-shadow:0 -2px 6px rgba(56,189,248,0.6); opacity:0; transform:scaleY(0); transform-origin:bottom; transition:opacity 0.18s ease,transform 0.18s ease; }
    .eye.wink-active .eye-pupil { opacity:0; transform:scaleY(0.1); }
    .eye.wink-active .eye-wink-shape { opacity:1; transform:scaleY(1); }
    .talking .eye-left .eye-pupil  { animation:pupilTalkLeft 1.2s infinite; }
    .talking .eye-left .eye-wink-shape { animation:winkTalkLeft 1.2s infinite; }
    .talking .eye-right .eye-pupil { animation:pupilTalkRight 1.5s infinite; }
    .talking .eye-right .eye-wink-shape { animation:winkTalkRight 1.5s infinite; }
    @keyframes pupilTalkLeft  { 0%,40%,100%{opacity:1;transform:scale(1);} 45%,95%{opacity:0;transform:scaleY(0.1);} }
    @keyframes winkTalkLeft   { 0%,40%,100%{opacity:0;transform:scaleY(0);} 45%,95%{opacity:1;transform:scaleY(1);} }
    @keyframes pupilTalkRight { 0%,50%,100%{opacity:1;transform:scale(1);} 55%,95%{opacity:0;transform:scaleY(0.1);} }
    @keyframes winkTalkRight  { 0%,50%,100%{opacity:0;transform:scaleY(0);} 55%,95%{opacity:1;transform:scaleY(1);} }

    /* Boca */
    .mouth { width:24px; height:12px; border:3.5px solid #888; border-radius:0 0 8px 8px; border-top:none; background:#161616; position:relative; margin-top:10px; box-shadow:0 2px 4px rgba(0,0,0,0.5); transition:all 0.25s cubic-bezier(0.175,0.885,0.32,1.275); z-index:2; }
    .mouth::before,.mouth::after { content:""; position:absolute; width:4px; height:6px; background:#fff; border:1.5px solid #161616; top:-1px; }
    .mouth::before { left:5px; } .mouth::after { right:5px; }
    .mouth.happy-mouth { width:28px; height:14px; border-radius:0 0 10px 10px; }
    .talking .mouth { animation:mouthTalk 0.16s infinite alternate ease-in-out; }
    @keyframes mouthTalk { 0%{width:20px;height:10px;border-radius:0 0 8px 8px;} 100%{width:26px;height:14px;border-radius:0 0 10px 10px;} }

    /* Puntos de pensamiento */
    .thought-dots { position:absolute; right:110px; bottom:105px; display:flex; flex-direction:row-reverse; align-items:flex-end; gap:6px; pointer-events:none; opacity:0; transition:opacity 0.25s ease; z-index:4; }
    .thought-dots.active { opacity:1; }
    .tdot { background:rgba(255,255,255,0.82); backdrop-filter:blur(10px); border:2.5px solid #0F172A; border-radius:50%; box-shadow:2px 2px 0px rgba(15,23,42,0.15); transform:scale(0); transition:transform 0.25s cubic-bezier(0.175,0.885,0.32,1.275); }
    .thought-dots.active .tdot-2 { transform:scale(1); transition-delay:0.0s; }
    .thought-dots.active .tdot-1 { transform:scale(1); transition-delay:0.06s; }
    .tdot-1{width:14px;height:14px;} .tdot-2{width:8px;height:8px;}

    /* Globo principal */
    .thought-bubble {
        position:absolute; right:125px;
        background:rgba(255,255,255,0.95);
        backdrop-filter:blur(12px);
        border:3px solid #0F172A; border-radius:20px;
        width:500px; padding:14px; box-sizing:border-box;
        box-shadow:5px 5px 0px rgba(15,23,42,0.2);
        opacity:0; transform:scale(0.7) translate(30px,10px);
        pointer-events:none;
        transition:opacity 0.15s cubic-bezier(0.175,0.885,0.32,1.275),
                    transform 0.15s cubic-bezier(0.175,0.885,0.32,1.275);
        z-index:5;
        max-height: 750px;
        overflow-y:auto;
    }
    .thought-bubble::-webkit-scrollbar{width:6px;}
    .thought-bubble::-webkit-scrollbar-track{background:transparent;}
    .thought-bubble::-webkit-scrollbar-thumb{background:rgba(15,23,42,0.2);border-radius:3px;}
    .thought-bubble.active { opacity:1; transform:scale(1) translate(0,0); pointer-events:auto; transition-delay:0s; }
    .toast-bubble { bottom:120px; height:auto; min-height:80px; max-height: 750px; }
    .bubble-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; color:#0F172A; font-size:20px; font-weight:bold; }
    .btn-close { background:transparent; border:none; color:#64748B; font-weight:bold; font-size:22px; cursor:pointer; transition:color 0.2s; }
    .btn-close:hover { color:#EF4444; }
    .toast-category { font-size:11px; font-weight:900; color:#64748B; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px; border-bottom:1.5px dashed #E2E8F0; padding-bottom:6px; }
    .toast-content { color:#0F172A; font-size:15px; font-weight:600; line-height:1.5; white-space:pre-line; }

    /* Chat messages */
    .msg-list { display:flex; flex-direction:column; gap:8px; margin-bottom:10px; max-height:600px; overflow-y:auto; }
    .msg-list::-webkit-scrollbar{width:5px;} .msg-list::-webkit-scrollbar-thumb{background:rgba(15,23,42,0.2);border-radius:3px;}
    .msg-bot { align-self:flex-start; background:#EFF6FF; border:1.5px solid #BFDBFE; border-radius:12px; border-top-left-radius:2px; padding:10px 12px; font-size:14px; font-weight:600; color:#1E3A5F; line-height:1.4; max-width:92%; white-space:pre-line; }
    .msg-user { align-self:flex-end; background:#4F46E5; border-radius:12px; border-top-right-radius:2px; padding:10px 12px; font-size:14px; font-weight:700; color:#fff; max-width:80%; }

    /* Input chat */
    .chat-input-row { display:flex; gap:6px; margin-top:6px; }
    .input-field { flex:1; background:#F1F5F9; border:2px solid #0F172A; border-radius:8px; padding:8px 12px; box-sizing:border-box; color:#0F172A; font-size:14px; font-weight:600; outline:none; transition:border-color 0.2s; }
    .input-field:focus { background:#fff; border-color:#4F46E5; }
    .btn-send { background:#4F46E5; color:#fff; font-weight:900; font-size:16px; border:2px solid #0F172A; border-radius:8px; padding:8px 14px; cursor:pointer; box-shadow:2px 2px 0px #0F172A; transition:transform 0.1s,box-shadow 0.1s,background 0.2s; }
    .btn-send:hover { background:#6366F1; }
    .btn-send:active { transform:translate(1px,1px); box-shadow:1px 1px 0px #0F172A; }

    /* Sugerencias */
    .sugerencias { display:flex; flex-wrap:wrap; gap:5px; margin-top:8px; }
    .sug-btn { background:#F8FAFC; border:1.5px solid #CBD5E1; border-radius:20px; padding:4px 10px; font-size:12px; font-weight:700; color:#334155; cursor:pointer; transition:background 0.15s; }
    .sug-btn:hover { background:#E2E8F0; }

    /* Tutor progress */
    .tutor-bar { display:none; align-items:center; gap:8px; margin-bottom:8px; }
    .tutor-bar.active { display:flex; }
    .tutor-progress { flex:1; height:6px; background:#E2E8F0; border-radius:3px; overflow:hidden; }
    .tutor-fill { height:100%; background:#4F46E5; border-radius:3px; transition:width 0.4s ease; }
    .tutor-label { font-size:11px; font-weight:700; color:#64748B; white-space:nowrap; }
    .btn-tutor-skip { background:transparent; border:1.5px solid #CBD5E1; border-radius:6px; padding:3px 8px; font-size:11px; font-weight:700; color:#94A3B8; cursor:pointer; }
    .btn-tutor-skip:hover { color:#EF4444; border-color:#EF4444; }
</style>
</head>
<body>
<div class="app-container">
  <div id="dots" class="thought-dots">
    <div class="tdot tdot-1"></div>
    <div class="tdot tdot-2"></div>
  </div>
  <div id="toastBubble" class="thought-bubble toast-bubble">
    <div class="bubble-header">
      <span>📖 Asistente CobroFacil</span>
      <button class="btn-close" onclick="cerrar()">✕</button>
    </div>
    <div id="tutorBar" class="tutor-bar">
      <span class="tutor-label" id="tutorLabel">Paso 1/15</span>
      <div class="tutor-progress"><div class="tutor-fill" id="tutorFill" style="width:0%"></div></div>
      <button class="btn-tutor-skip" onclick="skipTutor()">Saltar</button>
    </div>
    <div class="msg-list" id="msgList"></div>
    <div class="sugerencias" id="sugerencias">
      <button class="sug-btn" onclick="preguntar('atajos de teclado')">⌨️ Atajos</button>
      <button class="sug-btn" onclick="preguntar('como cobro')">💳 Cobrar</button>
      <button class="sug-btn" onclick="preguntar('balanza')">⚖️ Balanza</button>
      <button class="sug-btn" onclick="preguntar('cerrar turno')">🏁 Cierre</button>
      <button class="sug-btn" onclick="preguntar('cajon abierto')">🚨 Cajón</button>
      <button class="sug-btn" onclick="iniciarTutor()">🎓 Tutorial</button>
    </div>
    <div class="chat-input-row">
      <input type="text" id="chatInput" class="input-field" placeholder="Escribí tu consulta..."
             onkeypress="if(event.key==='Enter') enviar()">
      <button class="btn-send" onclick="enviar()">➤</button>
    </div>
  </div>
  <div id="robot" class="robot-head">
    <div class="antenna">
      <div class="antenna-shaft"></div>
      <div class="antenna-ball"></div>
    </div>
    <div class="orbit-ring"></div>
    <div class="visor">
      <div class="blush blush-left"></div>
      <div class="blush blush-right"></div>
      <div class="eyes-container">
        <div id="eyeLeft"  class="eye eye-left"><div class="eye-pupil"></div><div class="eye-wink-shape"></div></div>
        <div id="eyeRight" class="eye eye-right"><div class="eye-pupil"></div><div class="eye-wink-shape"></div></div>
      </div>
      <div id="mouth" class="mouth"></div>
    </div>
  </div>
</div>
<script>
const robot   = document.getElementById("robot");
const mouth   = document.getElementById("mouth");
const eyeL    = document.getElementById("eyeLeft");
const eyeR    = document.getElementById("eyeRight");
const bubble  = document.getElementById("toastBubble");
const msgList = document.getElementById("msgList");
const dots    = document.getElementById("dots");
const tutorBar  = document.getElementById("tutorBar");
const tutorFill = document.getElementById("tutorFill");
const tutorLabel= document.getElementById("tutorLabel");

let bubbleOpen   = false;
let tutorRunning = false;
let tutorIdx     = 0;

function blink() {
  if (!robot.classList.contains("talking")) {
    eyeL.classList.add("blinking"); eyeR.classList.add("blinking");
    setTimeout(()=>{ eyeL.classList.remove("blinking"); eyeR.classList.remove("blinking"); }, 150);
  }
  setTimeout(blink, 3000 + Math.random()*4000);
}
function wink() {
  if (!robot.classList.contains("talking")) {
    const left = Math.random()>0.5;
    const eye  = left ? eyeL : eyeR;
    eye.classList.add("wink-active"); mouth.classList.add("happy-mouth");
    setTimeout(()=>{ eye.classList.remove("wink-active"); mouth.classList.remove("happy-mouth"); }, 1200);
  }
  setTimeout(wink, 7000 + Math.random()*6000);
}
setTimeout(blink, 2000); setTimeout(wink, 5000);
robot.addEventListener("mouseenter",()=>{ eyeL.classList.add("wink-active"); eyeR.classList.add("wink-active"); mouth.classList.add("happy-mouth"); });
robot.addEventListener("mouseleave",()=>{ if(!robot.classList.contains("talking")){ eyeL.classList.remove("wink-active"); eyeR.classList.remove("wink-active"); mouth.classList.remove("happy-mouth"); } });

function hablar(on) {
  if(on) robot.classList.add("talking");
  else   robot.classList.remove("talking");
}

function toggleBubble() {
  bubbleOpen = !bubbleOpen;
  if(bubbleOpen) { 
      bubble.classList.add("active"); dots.classList.remove("active"); 
      console.log("resize://expand");
  }
  else { 
      bubble.classList.remove("active"); 
      console.log("resize://shrink");
  }
}
function cerrar() { 
    bubbleOpen=false; 
    bubble.classList.remove("active"); 
    console.log("resize://shrink");
}

let isDragging = false;
let dragX = 0, dragY = 0;
let clickStart = 0;

robot.addEventListener("mousedown", (e) => {
  if (e.button !== 0) return;
  isDragging = true;
  dragX = e.screenX;
  dragY = e.screenY;
  clickStart = Date.now();
});

window.addEventListener("mousemove", (e) => {
  if (isDragging) {
    let dx = e.screenX - dragX;
    let dy = e.screenY - dragY;
    dragX = e.screenX;
    dragY = e.screenY;
    if (dx !== 0 || dy !== 0) {
      console.log("move://" + dx + "," + dy);
    }
  }
});

window.addEventListener("mouseup", (e) => {
  if (isDragging) {
    isDragging = false;
    if (Date.now() - clickStart < 500) {
      toggleBubble();
    }
  }
});

function addMsg(txt, esBot) {
  const d = document.createElement("div");
  d.className = esBot ? "msg-bot" : "msg-user";
  d.textContent = txt;
  msgList.appendChild(d);
  msgList.scrollTop = msgList.scrollHeight;
}

function recibirRespuesta(respuesta) {
  hablar(false);
  dots.classList.remove("active");
  addMsg(respuesta, true);
}

function enviar() {
  const inp = document.getElementById("chatInput");
  const txt = inp.value.trim();
  if(!txt) return;
  inp.value = "";
  preguntar(txt);
}
function preguntar(txt) {
  if(!bubbleOpen) { 
      bubbleOpen=true; bubble.classList.add("active"); 
      console.log("resize://expand");
  }
  addMsg(txt, false);
  hablar(true);
  dots.classList.add("active");
  console.log("query://" + encodeURIComponent(txt));
}

function iniciarTutor() {
  tutorRunning = true; tutorIdx = 0;
  tutorBar.classList.add("active");
  if(!bubbleOpen){ 
      bubbleOpen=true; bubble.classList.add("active"); 
      console.log("resize://expand");
  }
  nextTutorStep();
}
function nextTutorStep() {
  console.log("tutor://next?idx=" + tutorIdx);
}
function recibirPasoTutor(msg, idx, total) {
  addMsg(msg, true);
  tutorFill.style.width = ((idx/total)*100) + "%";
  tutorLabel.textContent = "Paso " + idx + "/" + total;
  hablar(true);
  setTimeout(()=>hablar(false), 1500);
}
function tutorFin() {
  tutorRunning = false;
  tutorBar.classList.remove("active");
  addMsg("✅ ¡Tutorial completado! Ahora podés consultarme lo que necesites.", true);
}
function skipTutor() {
  tutorRunning = false;
  tutorBar.classList.remove("active");
  addMsg("⏭️ Tutorial omitido. ¡Estoy disponible para tus consultas!", true);
  console.log("tutor://skip");
}

setTimeout(()=>{
  addMsg("👋 ¡Hola! Soy tu asistente de CobroFacil POS. Hacé clic en 🎓 Tutorial para empezar.", true);
}, 300);
</script>
</body>
</html>
"""

from PyQt6.QtNetwork import QUdpSocket

class ChatAnimadoStandalone(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.resize(150, 150)
        self.motor = ChatManual()
        self._tutor_idx = 0
        self._tutor_activo = False
        self._tutor_timer = QTimer(self)
        self._tutor_timer.setSingleShot(True)
        self._tutor_timer.timeout.connect(self._tutor_avanzar)
        
        # UDP listener para F10
        self.udp_socket = QUdpSocket(self)
        self.udp_socket.bind(QHostAddress.AnyIPv4, 45680, QUdpSocket.ShareAddress | QUdpSocket.ReuseAddressHint)
        self.udp_socket.readyRead.connect(self._process_udp)
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.web = QWebEngineView()
        self.web.setPage(self._make_page())
        self.web.page().setBackgroundColor(Qt.transparent)
        self.web.setHtml(HTML_CHAT, QUrl("about:blank"))
        lay.addWidget(self.web, 1)
        
        # En lugar de hide() que congela Chromium, lo enviamos fuera de pantalla
        screen = QApplication.primaryScreen().geometry()
        self.pos_oculta = (-2000, -2000)
        self.pos_visible = (screen.right() - 170, screen.bottom() - 170)
        
        self.move(self.pos_oculta[0], self.pos_oculta[1])
        QTimer.singleShot(500, lambda: self.web.page().runJavaScript("cerrar();"))

    def _process_udp(self):
        while self.udp_socket.hasPendingDatagrams():
            data, host, port = self.udp_socket.readDatagram(self.udp_socket.pendingDatagramSize())
            msg = data.data().decode('utf-8', errors='ignore')
            if msg == "TOGGLE":
                if self.x() < 0:
                    self.move(self.pos_visible[0], self.pos_visible[1])
                    self.raise_()
                    self.activateWindow()
                self.web.page().runJavaScript("toggleBubble();")
            elif msg == "HIDE":
                self.move(self.pos_oculta[0], self.pos_oculta[1])
            elif msg.startswith("TICKET_UPDATE|"):
                partes = msg.split("|")
                if len(partes) >= 2:
                    total = partes[1]
                    self.web.page().runJavaScript(f"recibirRespuesta('🛒 Ticket actualizado.\\nTotal actual: {total}');")
                    if self.x() < 0:
                        self.move(self.pos_visible[0], self.pos_visible[1])
                        self.raise_()
                        self.activateWindow()

    def _make_page(self):
        page = QWebEnginePage(self.web)
        connect_webengine_console(page, self._on_js_message)
        webengine_page_transparent(page)
        return page

    def _on_js_message(self, level, message, line, source):
        if message.startswith("query://"):
            from urllib.parse import unquote
            q = unquote(message.replace("query://", ""))
            resp = self.motor.consultar(q)
            self._responder_js(resp)
        elif message.startswith("tutor://next"):
            idx = int(message.split("idx=")[1])
            self._tutor_idx = idx
            self._tutor_avanzar()
        elif message.startswith("tutor://skip"):
            self._tutor_activo = False
            self._tutor_timer.stop()
        elif message.startswith("resize://"):
            action = message.replace("resize://", "")
            if action == "expand":
                self.resize_window_dynamic(True)
            elif action == "shrink":
                self.resize_window_dynamic(False)
        elif message.startswith("move://"):
            parts = message.replace("move://", "").split(",")
            dx, dy = int(parts[0]), int(parts[1])
            self.move(self.x() + dx, self.y() + dy)

    def _responder_js(self, texto):
        import json
        t = json.dumps(texto)
        self.web.page().runJavaScript(f"recibirRespuesta({t});")

    def resize_window_dynamic(self, expand: bool):
        current_geom = self.geometry()
        if expand:
            # Expandir hacia arriba y a la izquierda
            new_w, new_h = 700, 980
            if self.width() != new_w:
                self.setGeometry(current_geom.right() - new_w + 1, current_geom.bottom() - new_h + 1, new_w, new_h)
        else:
            # Encoger hacia abajo y a la derecha
            new_w, new_h = 150, 150
            if self.width() != new_w:
                self.setGeometry(current_geom.right() - new_w + 1, current_geom.bottom() - new_h + 1, new_w, new_h)

    def _tutor_avanzar(self):
        if self._tutor_idx >= len(PASOS_TUTOR):
            self._tutor_activo = False
            self.web.page().runJavaScript("tutorFin();")
            return
        
        paso = PASOS_TUTOR[self._tutor_idx]
        msg_json = json.dumps(paso["msg"])
        self.web.page().runJavaScript(f"recibirPasoTutor({msg_json}, {self._tutor_idx + 1}, {len(PASOS_TUTOR)});")
        self._tutor_idx += 1
        self._tutor_timer.start(paso["espera"] * 1000)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = ChatAnimadoStandalone()
    widget.show()
    sys.exit(qt_exec(app))