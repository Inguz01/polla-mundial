from datetime import datetime, timedelta
import pytz


# ==============================
# ⏰ VALIDAR SI APUESTA ESTÁ ABIERTA
# ==============================
def apuesta_abierta(fecha, hora, estado=None):

    # si ya está marcado como cerrado o liquidado → bloquear
    if estado in ["cerrado", "liquidado"]:
        return False

    try:
        fecha_hora = datetime.strptime(
            f"{fecha} {hora}",
            "%Y-%m-%d %H:%M"
        )

        limite = fecha_hora - timedelta(minutes=5)

        # usar hora de Colombia para no bloquear 5h antes en servidores UTC
        tz = pytz.timezone("America/Bogota")
        ahora = datetime.now(tz).replace(tzinfo=None)

        return ahora < limite

    except:
        # si hay error en datos → mejor bloquear
        return False


# ==============================
# 🔢 VALIDAR GOLES
# ==============================
def validar_goles(goles):

    try:
        g = int(goles)
    except:
        return False

    if g < 0 or g > 20:
        return False

    return True


# ==============================
# 🔢 VALIDAR MARCADOR COMPLETO
# ==============================
def validar_marcador(local, visitante):

    if not validar_goles(local):
        return False

    if not validar_goles(visitante):
        return False

    return True


# ==============================
# 💰 VALIDAR MONTO
# ==============================
def validar_monto(monto):

    try:
        m = float(monto)
    except:
        return False

    if m <= 0:
        return False

    return True