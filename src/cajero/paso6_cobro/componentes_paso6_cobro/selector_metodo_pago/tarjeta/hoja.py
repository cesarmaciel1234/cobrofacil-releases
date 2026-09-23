"""El aspecto de una tarjeta en reposo y marcada."""


def estilo_tarjeta(oscuro):
    if oscuro:
        return """
            QFrame#Paso6TarjetaMetodo {
                background: #1E293B;
                border: 1px solid #334155;
                border-radius: 16px;
            }
            QFrame#Paso6TarjetaMetodo[active="true"] {
                background: #1E293B;
                border: 2px solid #F8FAFC;
            }
            QFrame#Paso6TarjetaMetodo:hover {
                border-color: #64748B;
            }
        """
    return """
        QFrame#Paso6TarjetaMetodo {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 16px;
        }
        QFrame#Paso6TarjetaMetodo[active="true"] {
            background: #F8FAFC;
            border: 2px solid #15293C;
        }
        QFrame#Paso6TarjetaMetodo:hover {
            border-color: #94A3B8;
        }
    """
