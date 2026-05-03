import streamlit as st
import pandas as pd

from utils.data_loader import cargar_todo
from utils.dataframe_utils import safe_int
from services.calculo_puntos import calcular_puntos
from utils.config import valor_apuesta_por_fase, porcentaje_admin


def ranking_page():

    st.title("Tabla de posiciones")

    data = cargar_todo()

    df_pred = data["predicciones"].copy()
    df_res = data["resultados"].copy()
    df_part = data["partidos"].copy()

    if len(df_pred) == 0:
        st.info("Aún no hay predicciones")
        return

    # =========================
    # JOIN DATOS
    # =========================

    df = df_pred.merge(
        df_res,
        on="partido_id",
        suffixes=("_pred", "_real"),
        how="left"
    )

    df = df.merge(
        df_part[["id", "fase"]],
        left_on="partido_id",
        right_on="id",
        how="left"
    )

    # =========================
    # LIMPIEZA
    # =========================

    # 🔥 asegurar columnas antes de usarlas
    from utils.dataframe_utils import asegurar_columnas

    df = asegurar_columnas(
        df,
        [
            "goles_local_pred",
            "goles_visitante_pred",
            "goles_local_real",
            "goles_visitante_real"
        ]
    )

    for col in [
        "goles_local_pred",
        "goles_visitante_pred",
        "goles_local_real",
        "goles_visitante_real"
    ]:
        df[col] = df[col].apply(safe_int)

    # =========================
    # PUNTOS
    # =========================

    def calcular_si_terminado(row):
        if pd.isna(row["goles_local_real"]) or pd.isna(row["goles_visitante_real"]):
            return 0

        return calcular_puntos(
            row["goles_local_pred"],
            row["goles_visitante_pred"],
            row["goles_local_real"],
            row["goles_visitante_real"],
            row.get("participa", 1)
        )

    df["puntos"] = df.apply(calcular_si_terminado, axis=1)

    df["exacto"] = df.apply(
        lambda x: 1 if (
            pd.notna(x["goles_local_real"]) and
            pd.notna(x["goles_visitante_real"]) and
            x["goles_local_pred"] == x["goles_local_real"] and
            x["goles_visitante_pred"] == x["goles_visitante_real"]
        ) else 0,
        axis=1
    )

    # =========================
    # EXACTOS
    # =========================

    def calcular_si_terminado(row):
        if pd.isna(row["goles_local_real"]) or pd.isna(row["goles_visitante_real"]):
            return 0

        return calcular_puntos(
            row["goles_local_pred"],
            row["goles_visitante_pred"],
            row["goles_local_real"],
            row["goles_visitante_real"],
            row.get("participa", 1)
        )

    df["puntos"] = df.apply(calcular_si_terminado, axis=1)

    # =========================
    # AGRUPAR
    # =========================

    tabla = df.groupby("usuario_id").agg({
        "puntos": "sum",
        "exacto": "sum"
    }).reset_index()

    # =========================
    # ORDEN
    # =========================

    tabla = tabla.sort_values(
        by=["puntos", "exacto"],
        ascending=False
    )

    tabla.insert(0, "posicion", range(1, len(tabla) + 1))

    # =========================
    # 💰 JACKPOT
    # =========================

    df_pred_part = df_pred.copy()

    df_pred_part = df_pred_part.merge(
        df_part[["id", "fase"]],
        left_on="partido_id",
        right_on="id",
        how="left"
    )

    df_pred_part["valor"] = df_pred_part["fase"].apply(
        lambda x: valor_apuesta_por_fase(str(x)) if pd.notna(x) else 0
    )

    total_recaudado = df_pred_part["valor"].sum()
    comision = total_recaudado * porcentaje_admin()
    jackpot = total_recaudado - comision

    st.metric("Jackpot acumulado", f"${jackpot:,.0f}")

    st.divider()

    # =========================
    # MOSTRAR
    # =========================

    st.dataframe(tabla, use_container_width=True)