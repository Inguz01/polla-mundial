import streamlit as st
import pandas as pd
from utils.data_loader import cargar_todo
from services.calculo_puntos import calcular_puntos
from utils.dataframe_utils import (
    safe_int,
    asegurar_columnas
)


def historial_page():

    st.title("Mi historial de apuestas")

    usuario_actual = st.session_state.get("usuario")

    if not usuario_actual:
        st.error("Sesión no válida")
        st.stop()

    # ===== carga centralizada =====

    data = cargar_todo()

    df_pred = data["predicciones"].copy()
    df_res = data["resultados"].copy()
    df_part = data["partidos"].copy()

    # ==============================

    if st.session_state.get("rol") == "admin":
        st.warning("Este módulo es solo para participantes")
        st.stop()

    if len(df_pred) == 0:
        st.info("Aún no tienes apuestas")
        return

    df_pred = df_pred[
        df_pred["usuario_id"] == usuario_actual
    ]

    if len(df_pred) == 0:
        st.info("Aún no tienes apuestas")
        return

    # asegurar columnas necesarias

    df_pred = asegurar_columnas(
        df_pred,
        ["usuario_id", "partido_id", "goles_local", "goles_visitante"]
    )

    df_res = asegurar_columnas(
        df_res,
        ["partido_id", "goles_local", "goles_visitante"]
    )

    # unir datos

    df = df_pred.merge(
        df_res,
        on="partido_id",
        suffixes=("_pred", "_real"),
        how="left"
    )

    df = df.merge(
        df_part[
            ["id", "equipo_local", "equipo_visitante", "fecha"]
        ],
        left_on="partido_id",
        right_on="id",
        how="left"
    )

    # =========================
    # detectar si el partido terminó
    # =========================

    df["partido_finalizado"] = (
        df["goles_local_real"].notna() &
        df["goles_visitante_real"].notna()
    )

    # =========================
    # LIMPIEZA
    # =========================

    for col in [
        "goles_local_pred",
        "goles_visitante_pred",
        "goles_local_real",
        "goles_visitante_real"
    ]:
        df[col] = df[col].apply(safe_int)

    df["participa"] = df["participa"].apply(safe_int)

    # =========================
    # PUNTOS SOLO SI TERMINÓ
    # =========================

    def calcular_si_terminado(row):
        if not row["partido_finalizado"]:
            return None

        return calcular_puntos(
            row["goles_local_real"],
            row["goles_visitante_real"],
            row["goles_local_pred"],
            row["goles_visitante_pred"],
            row["participa"]
        )

    df["puntos"] = df.apply(calcular_si_terminado, axis=1)

    # =========================
    # FORMATO
    # =========================

    df["partido"] = (
        df["equipo_local"] + " vs " + df["equipo_visitante"]
    )

    df["prediccion"] = (
        df["goles_local_pred"].astype(str)
        + " - "
        + df["goles_visitante_pred"].astype(str)
    )

    # 🔥 RESULTADO SOLO SI TERMINÓ

    df["resultado"] = df.apply(
        lambda x: f"{x['goles_local_real']}-{x['goles_visitante_real']}"
        if x["partido_finalizado"]
        else "-",
        axis=1
    )

    # =========================
    # PREMIOS
    # =========================

    df["premio"] = None

    df_mov = data.get("movimientos", pd.DataFrame())

    # si está vacío → crear estructura válida
    if df_mov is None or df_mov.empty:
        df_mov = pd.DataFrame(columns=[
            "usuario_id",
            "tipo",
            "referencia",
            "monto"
        ])

    # compatibilidad (por si hay datos viejos)
    if "usuario_id" not in df_mov.columns and "usuario" in df_mov.columns:
        df_mov["usuario_id"] = df_mov["usuario"]

    # asegurar columnas mínimas
    for col in ["usuario_id", "tipo", "referencia", "monto"]:
        if col not in df_mov.columns:
            df_mov[col] = None

    for i, row in df.iterrows():

        if not row["partido_finalizado"]:
            continue

        mov = df_mov[
            (df_mov["usuario_id"] == usuario_actual) &
            (df_mov["referencia"] == f"partido_{row['partido_id']}") &
            (df_mov["tipo"] == "premio")
        ]

        if len(mov) > 0:
            df.at[i, "premio"] = float(mov["monto"].sum())

    # =========================
    # TABLA FINAL
    # =========================

    tabla = df[
        [
            "fecha",
            "partido",
            "prediccion",
            "resultado",
            "puntos",
            "premio"
        ]
    ].sort_values(by="fecha")

    st.dataframe(tabla, use_container_width=True)