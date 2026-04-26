import pandas as pd
from utils.config import valor_apuesta_por_fase, porcentaje_admin
from utils.movimientos import registrar_movimiento
from utils.data_loader import cargar_todo


def calcular_premio_partido(partido_id):

    data = cargar_todo()

    df_pred = data["predicciones"]
    df_res = data["resultados"]
    df_part = data["partidos"]
    df_mov = data["movimientos"]

    # =========================
    # PARTIDO
    # =========================

    df_partido = df_part[df_part["id"].astype(str) == str(partido_id)]

    if len(df_partido) == 0:
        return None

    fase = df_partido.iloc[0]["fase"]

    # =========================
    # PREDICCIONES
    # =========================

    df_pred_part = df_pred[
        df_pred["partido_id"].astype(str) == str(partido_id)
    ]

    participantes = len(df_pred_part)

    if participantes == 0:
        return None

    # =========================
    # POZO
    # =========================

    valor = valor_apuesta_por_fase(fase)

    pozo_bruto = participantes * valor
    comision = pozo_bruto * porcentaje_admin()
    pozo = pozo_bruto - comision

    # =========================
    # RESULTADO REAL
    # =========================

    df_res_part = df_res[
        df_res["partido_id"].astype(str) == str(partido_id)
    ]

    if len(df_res_part) == 0:
        return None

    real_local = int(df_res_part.iloc[0]["goles_local"])
    real_visit = int(df_res_part.iloc[0]["goles_visitante"])

    # =========================
    # 🔄 REVERSO (SI YA HABÍA PAGOS)
    # =========================

    pagos_previos = df_mov[
        (df_mov["referencia"] == f"partido_{partido_id}")
        &
        (df_mov["tipo"] == "premio")
    ]

    if len(pagos_previos) > 0:

        for _, mov in pagos_previos.iterrows():

            registrar_movimiento(
                mov["usuario_id"],
                "reverso_premio",
                f"partido_{partido_id}",   # 👈 misma referencia
                -float(mov["monto"])
            )

    # =========================
    # GANADORES
    # =========================

    ganadores = df_pred_part[
        (df_pred_part["goles_local"].astype(int) == real_local)
        &
        (df_pred_part["goles_visitante"].astype(int) == real_visit)
    ]

    num_ganadores = len(ganadores)

    if num_ganadores > 0:

        premio_por_usuario = pozo / num_ganadores

        for _, g in ganadores.iterrows():

            registrar_movimiento(
                g["usuario_id"],
                "premio",
                f"partido_{partido_id}",
                premio_por_usuario
            )

        return {
            "tipo": "repartido",
            "pozo": pozo,
            "ganadores": num_ganadores,
            "premio": premio_por_usuario
        }

    else:

        return {
            "tipo": "acumulado",
            "pozo": pozo,
            "ganadores": 0,
            "premio": 0
        }