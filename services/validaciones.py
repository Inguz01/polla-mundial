from datetime import datetime, timedelta

from config.settings import MINUTOS_CIERRE


def partido_abierto(fecha, hora):

    cierre = datetime.strptime(
        f"{fecha} {hora}",
        "%Y-%m-%d %H:%M"
    ) - timedelta(minutes=MINUTOS_CIERRE)

    return datetime.now() < cierre