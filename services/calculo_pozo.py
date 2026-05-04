from settings import PORCENTAJE_ADMIN


def calcular_pozo(total_recaudado):
    try:
        total = float(total_recaudado)
    except:
        total = 0

    if total < 0:
        total = 0

    admin = round(total * PORCENTAJE_ADMIN, 2)
    pozo = round(total - admin, 2)

    return admin, pozo


def liquidar_partido(df_apuestas_partido, resultado_real, jackpot_actual=0):

    total_apostado = df_apuestas_partido["valor"].sum()

    admin, bolsa = calcular_pozo(total_apostado)

    ganadores = df_apuestas_partido[
        df_apuestas_partido["prediccion"] == resultado_real
    ]

    num_ganadores = len(ganadores)

    transacciones = []

    # =========================
    # COMISIÓN (SIEMPRE)
    # =========================

    transacciones.append({
        "usuario_id": "admin",
        "tipo": "comision",
        "monto": admin,
        "descripcion": "Comisión partido"
    })

    # =========================
    # CASO: HAY GANADORES
    # =========================

    if num_ganadores > 0:

        premio_por_usuario = bolsa / num_ganadores

        for _, row in ganadores.iterrows():
            transacciones.append({
                "usuario_id": row["usuario"],
                "tipo": "premio",
                "monto": round(premio_por_usuario, 2),
                "descripcion": "Premio partido"
            })

        # pagar jackpot si existe
        if jackpot_actual > 0:

            extra = jackpot_actual / num_ganadores

            for _, row in ganadores.iterrows():
                transacciones.append({
                    "usuario_id": row["usuario"],
                    "tipo": "jackpot_pago",
                    "monto": round(extra, 2),
                    "descripcion": "Pago jackpot"
                })

            jackpot_actual = 0

    # =========================
    # CASO: NO HAY GANADORES
    # =========================

    else:

        transacciones.append({
            "usuario_id": "sistema",
            "tipo": "jackpot_aporte",
            "monto": bolsa,
            "descripcion": "Aporte a jackpot"
        })

        jackpot_actual += bolsa

    return transacciones, jackpot_actual