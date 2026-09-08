/* Cinta duplicada: salta y se posa; al llegar a la copia, vuelve a la primera sin que se note. */

export function iniciarCintaInfinita(track, { xDeCuadro, periodoMs = 4000, ease = "transform 0.75s cubic-bezier(0.22, 1, 0.36, 1)", alPosar, inicio = 0 } = {}) {
    if (!track || track.children.length < 2) return;

    if (track._cinta) track._cinta.parar();

    const mitad = Math.floor(track.children.length / 2);
    let index = Math.min(Math.max(0, inicio), track.children.length - 1);
    let enCopia = false;

    const anchoCopia = () => {
        const a = track.children[0];
        const b = track.children[mitad];
        if (!a || !b) return 0;
        return b.offsetLeft - a.offsetLeft;
    };

    const pintar = (i, animar) => {
        const x = xDeCuadro(i);
        if (animar) track.style.transition = ease;
        else {
            track.style.transition = "none";
            void track.offsetWidth;
        }
        track.style.transform = `translate3d(${x}px, 0, 0)`;
        if (alPosar) alPosar(i, mitad);
    };

    const volverSinQueSeNote = () => {
        if (!enCopia || index < mitad) return;
        const delta = anchoCopia();
        const matrix = new DOMMatrix(getComputedStyle(track).transform);
        track.style.transition = "none";
        track.style.transform = `translate3d(${matrix.m41 + delta}px, 0, 0)`;
        void track.offsetWidth;
        index -= mitad;
        enCopia = false;
        if (alPosar) alPosar(index, mitad);
    };

    const onEnd = (ev) => {
        if (ev.target !== track || ev.propertyName !== "transform") return;
        volverSinQueSeNote();
    };
    track.addEventListener("transitionend", onEnd);

    pintar(0, false);

    const timer = setInterval(() => {
        index += 1;
        if (index >= track.children.length) index = mitad;
        enCopia = index >= mitad;
        pintar(index, true);
        window.setTimeout(volverSinQueSeNote, 900);
    }, periodoMs);

    track._cinta = {
        parar() {
            clearInterval(timer);
            track.removeEventListener("transitionend", onEnd);
            track._cinta = null;
        },
    };
}
