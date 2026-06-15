def calcular_puntos(
    goles_local_real,
    goles_visitante_real,
    goles_local_pred,
    goles_visitante_pred,
    participa
):

    if not participa:
        return 0

    # Marcador exacto
    if (
        goles_local_real == goles_local_pred
        and
        goles_visitante_real == goles_visitante_pred
    ):
        return 3

    ganador_real = goles_local_real - goles_visitante_real
    ganador_pred = goles_local_pred - goles_visitante_pred

    # Ambos pronosticaron empate
    if ganador_real == 0 and ganador_pred == 0:
        return 2

    # Acertó ganador
    if ganador_real * ganador_pred > 0:
        return 2

    return 1