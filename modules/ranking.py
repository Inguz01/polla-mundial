import streamlit as st
import pandas as pd

from utils.data_loader import cargar_todo
from utils.dataframe_utils import safe_int, asegurar_columnas
from services.calculo_puntos import calcular_puntos


def ranking_page():

    st.title("Tabla de posiciones")

    data = cargar_todo()

    df_pred = data["predicciones"].copy()
    df_res = data["resultados"].copy()
    df_part = data["partidos"].copy()
    df_mov = data["movimientos"].copy()

    # =========================
    # VALIDACIONES INICIALES
    # =========================

    if df_pred.empty:
        st.info("Aún no hay predicciones")
        return

    if df_res.empty:
        st.info("Aún no hay resultados registrados")
        return

    if "partido_id" not in df_pred.columns:
        st.error("Error en predicciones: falta partido_id")
        return

    if "partido_id" not in df_res.columns:
        st.error("Error en resultados: falta partido_id")
        return

    # =========================
    # JOIN SOLO PARTIDOS FINALIZADOS
    # =========================

    df = df_pred.merge(
        df_res,
        on="partido_id",
        suffixes=("_pred", "_real"),
        how="inner"  # 🔥 SOLO partidos con resultado
    )

    if df.empty:
        st.info("Aún no hay partidos finalizados")
        return

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
    # ELIMINAR DUPLICADOS
    # =========================

    df = df.drop_duplicates(
        subset=["usuario_id", "partido_id"],
        keep="last"
    )

    # =========================
    # CÁLCULO DE PUNTOS
    # =========================

    df["puntos"] = df.apply(
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

    df["exacto"] = (
        (df["goles_local_pred"] == df["goles_local_real"]) &
        (df["goles_visitante_pred"] == df["goles_visitante_real"])
    ).astype(int)

    # =========================
    # PARTIDOS JUGADOS
    # =========================

    df["jugado"] = 1

    # =========================
    # AGRUPAR POR USUARIO
    # =========================

    tabla = df.groupby("usuario_id").agg({
        "puntos": "sum",
        "exacto": "sum",
        "jugado": "sum"
    }).reset_index()

    tabla = tabla.rename(columns={
        "jugado": "partidos_jugados"
    })

    # =========================
    # RANKING CORRECTO (EMPATES)
    # =========================

    tabla = tabla.sort_values(
        by=["puntos", "exacto"],
        ascending=False
    )

    tabla["posicion"] = tabla["puntos"].rank(
        method="dense",
        ascending=False
    ).astype(int)

    tabla = tabla.sort_values(
        by=["posicion", "exacto"],
        ascending=[True, False]
    )

    # =========================
    # JACKPOT REAL DESDE MOVIMIENTOS
    # =========================

    if not df_mov.empty:

        df_mov["monto"] = pd.to_numeric(df_mov["monto"], errors="coerce").fillna(0)

        jackpot_aporte = df_mov[df_mov["tipo"] == "jackpot_aporte"]["monto"].sum()
        jackpot_pago = df_mov[df_mov["tipo"] == "jackpot_pago"]["monto"].sum()

        jackpot_total = jackpot_aporte - jackpot_pago

    else:
        jackpot_total = 0

    st.metric("Jackpot acumulado", f"${jackpot_total:,.0f}")

    st.divider()

    # =========================
    # MOSTRAR TABLA
    # =========================

    tabla = tabla[
        ["posicion", "usuario_id", "partidos_jugados", "puntos", "exacto"]
    ]

    # =========================
    # TOP 3
    # =========================

    top3 = tabla.head(3)

    medallas = {
        1: "🥇",
        2: "🥈",
        3: "🥉"
    }

    for _, row in top3.iterrows():

        posicion = int(row["posicion"])

        medalla = medallas.get(posicion, "🏅")

        with st.expander(
            f"{medalla} {row['usuario_id']} — ⭐ {row['puntos']} pts",
            expanded=False
        ):

            st.markdown(
                f"""
                🎯 **Exactos:** {row['exacto']}

                ⚽ **Partidos jugados:** {row['partidos_jugados']}
                """
            )

    # =========================
    # RESTO DEL RANKING
    # =========================

    resto = tabla.iloc[3:]

    if len(resto) > 0:

        st.divider()

        for _, row in resto.iterrows():

            with st.expander(
                f"#{row['posicion']} — {row['usuario_id']} | ⭐ {row['puntos']} pts"
            ):

                st.markdown(
                    f"""
                    🎯 **Exactos:** {row['exacto']}

                    ⚽ **Partidos jugados:** {row['partidos_jugados']}
                    """
                )