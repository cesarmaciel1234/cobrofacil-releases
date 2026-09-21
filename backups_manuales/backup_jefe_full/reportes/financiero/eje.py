"""Eje Y pegado al máximo real (sin saltar a 4M)."""


def maximo_eje(valores) -> float:
    nums = [float(v or 0) for v in valores]
    m = max(nums) if nums else 0.0
    if m <= 0:
        return 1.0
    techo = m * 1.08
    if techo < 10:
        return max(1.0, round(techo + 0.5))
    mag = 10 ** (len(str(int(techo))) - 1)
    pasos = (int(techo) // mag) + (1 if int(techo) % mag else 0)
    if pasos > 8:
        mag *= 2
        pasos = (int(techo) // mag) + (1 if int(techo) % mag else 0)
    return float(max(pasos, 1) * mag)
