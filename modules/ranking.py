import streamlit as st
import pandas as pd

from utils.data_loader import cargar_todo
from utils.dataframe_utils import safe_int, asegurar_columnas
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
    # LIMPIEZA SEGURA
    # =========================

    df = asegurar_columnas(
        df,
        [
            "usuario_id",
            "partido_id",
            "participa",
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
        "goles_visitante_real",
        "participa"
    ]:
        df[col] = df[col].apply(safe_int)

    # =========================
    # 🔥 FILTRAR SOLO FINALIZADOS
    # =========================

    df_finalizados = df[
        df["goles_local_real"].notna() &
        df["goles_visitante_real"].notna()
    ].copy()

    if len(df_finalizados) == 0:
        st.info("Aún no hay partidos finalizados")
        return

    # =========================
    # 🔥 EL FIX REAL (DUPLICADOS)
    # =========================

    df_finalizados = df_finalizados.drop_duplicates(
        subset=["usuario_id", "partido_id"],
        keep="last"
    )

    # =========================
    # PUNTOS
    # =========================

    df_finalizados["puntos"] = df_finalizados.apply(
        lambda x: calcular_puntos(
            x["goles_local_real"],
            x["goles_visitante_real"],
            x["goles_local_pred"],
            x["goles_visitante_pred"],
            x["participa"]
        ),
        axis=1
    )

    # =========================
    # EXACTOS
    # =========================

    df_finalizados["exacto"] = (
        (df_finalizados["goles_local_pred"] == df_finalizados["goles_local_real"]) &
        (df_finalizados["goles_visitante_pred"] == df_finalizados["goles_visitante_real"])
    ).astype(int)

    # =========================
    # PARTIDOS JUGADOS
    # =========================

    df_finalizados["jugado"] = 1

    # =========================
    # AGRUPAR
    # =========================

    tabla = df_finalizados.groupby("usuario_id").agg({
        "puntos": "sum",
        "exacto": "sum",
        "jugado": "sum"
    }).reset_index()

    tabla = tabla.rename(columns={
        "jugado": "partidos_jugados"
    })

    # =========================
    # ORDEN
    # =========================

    tabla = tabla.sort_values(
        by=["puntos", "exacto"],
        ascending=False
    )

    tabla.insert(0, "posicion", range(1, len(tabla) + 1))

    # =========================
    # 💰 JACKPOT (básico)
    # =========================

    df_pred_part = df_pred.merge(
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

    tabla = tabla[
        ["posicion", "usuario_id", "partidos_jugados", "puntos", "exacto"]
    ]

    st.dataframe(tabla, use_container_width=True)