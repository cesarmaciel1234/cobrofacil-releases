import re

with open("src/carteleria/lanzador_tv/la_cara_web/css/cards.css", "r", encoding="utf-8") as f:
    text = f.read()

replacement = """/* Barra de progreso */
.asian-rank-progress-container {
    background: var(--rank-bar-track);
    border-radius: 999px;
    height: 3.5cqh;
    min-height: 22px;
    position: relative;
    overflow: hidden;
    display: flex;
    align-items: center;
    margin-top: 0.8cqh;
}
.asian-rank-progress-bar {
    background: var(--rank-bar-bg);
    height: 100%;
    border-radius: 999px;
    transition: width 1s ease-out;
}
.asian-rank-tag {
    position: absolute;
    left: 1cqw;
    color: #EF4444;
    font-size: clamp(12px, 1.1cqw, 15px);
    font-weight: 900;
    text-shadow: 0 1px 4px rgba(0,0,0,0.8);
    letter-spacing: 0.05em;
    z-index: 2;
}"""

text = re.sub(r'/\* Barra de progreso \*/\s*\.asian-rank-progress-container \{.*?z-index:\s*2;\s*\}', replacement, text, flags=re.DOTALL)

with open("src/carteleria/lanzador_tv/la_cara_web/css/cards.css", "w", encoding="utf-8", newline="") as f:
    f.write(text)
