import streamlit as st
import pandas as pd

from utils.data_loader import cargar_todo


def safe_int(value):

    try:
        return int(float(value))
    except:
        return 0


def calcular_puntos(pred_local, pred_visit, real_local, real_visit):

    puntos = 1

    # exacto
    if pred_local == real_local and pred_visit == real_visit:
        return 3

    # resultado correcto
    if (
        (pred_local > pred_visit and real_local > real_visit)
        or
        (pred_local < pred_visit and real_local < real_visit)
        or
        (pred_local == pred_visit and real_local == real_visit)
    ):
        puntos += 1

    return puntos


def ranking_page():

    st.title("🏆 Tabla de posiciones")

    data = cargar_todo()

    df_pred = data["predicciones"].copy()
    df_res = data["resultados"].copy()

    if len(df_pred) == 0:
        st.warning("No hay predicciones")
        return

    if len(df_res) == 0:
        st.warning("Aún no hay resultados registrados")
        return

    # =========================
    # LIMPIEZA
    # =========================

    df_pred["partido_id"] = df_pred["partido_id"].astype(str)
    df_res["partido_id"] = df_res["partido_id"].astype(str)

    df_pred["goles_local"] = df_pred["goles_local"].apply(safe_int)
    df_pred["goles_visitante"] = df_pred["goles_visitante"].apply(safe_int)

    df_res["goles_local"] = df_res["goles_local"].apply(safe_int)
    df_res["goles_visitante"] = df_res["goles_visitante"].apply(safe_int)

    # =========================
    # MERGE
    # =========================

    df = df_pred.merge(
        df_res,
        on="partido_id",
        suffixes=("_pred", "_real")
    )

    if len(df) == 0:
        st.info("Aún no hay partidos con resultado")
        return

    # =========================
    # PUNTOS
    # =========================

    df["puntos"] = df.apply(
        lambda x: calcular_puntos(
            x["goles_local_pred"],
            x["goles_visitante_pred"],
            x["goles_local_real"],
            x["goles_visitante_real"]
        ),
        axis=1
    )

    # exactos
    df["exacto"] = (
        (df["goles_local_pred"] == df["goles_local_real"])
        &
        (df["goles_visitante_pred"] == df["goles_visitante_real"])
    ).astype(int)

    # =========================
    # AGRUPACIÓN
    # =========================

    tabla = df.groupby("usuario_id").agg(
        puntos=("puntos", "sum"),
        partidos=("partido_id", "count"),
        exactos=("exacto", "sum")
    ).reset_index()

    # =========================
    # ORDEN (CLAVE)
    # =========================

    tabla = tabla.sort_values(
        by=["puntos", "exactos"],  # desempate
        ascending=False
    )

    # =========================
    # POSICIÓN
    # =========================

    tabla.insert(
        0,
        "posicion",
        range(1, len(tabla) + 1)
    )

    # =========================
    # UI
    # =========================

    st.title("🏆 Ranking Jackpot")

    st.dataframe(
        tabla,
        use_container_width=True
    )