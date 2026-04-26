import streamlit as st
import pandas as pd
from utils.data_loader import cargar_todo
from utils.config import valor_apuesta_por_fase, porcentaje_admin


def dashboard_page():

    st.title("📊 Resumen de la Polla")

    data = cargar_todo()

    df_pred = data["predicciones"]
    df_res = data["resultados"]
    df_part = data["partidos"]
    df_mov = data["movimientos"]

    # =========================
    # CALCULO POR PARTIDO
    # =========================

    resumen = []

    for _, p in df_part.iterrows():

        partido_id = p["id"]

        pred = df_pred[
            df_pred["partido_id"].astype(str) == str(partido_id)
        ]

        participantes = len(pred)

        if participantes == 0:
            continue

        fase = p["fase"]
        valor = valor_apuesta_por_fase(fase)

        pozo_bruto = participantes * valor
        pozo = pozo_bruto * (1 - porcentaje_admin())

        pagos = df_mov[
            (df_mov["referencia"] == f"partido_{partido_id}")
            &
            (df_mov["tipo"] == "premio")
        ]

        ganadores = len(pagos)

        if ganadores > 0:
            premio = pagos["monto"].iloc[0]
        else:
            premio = 0

        resumen.append({

            "partido": f"{p['equipo_local']} vs {p['equipo_visitante']}",
            "fecha": p["fecha"],
            "participantes": participantes,
            "pozo": pozo,
            "ganadores": ganadores,
            "premio": premio

        })

    df = pd.DataFrame(resumen)

    if len(df) == 0:
        st.info("Aún no hay datos")
        return

    # =========================
    # JACKPOT
    # =========================

    sin_ganadores = df[df["ganadores"] == 0]

    jackpot = sin_ganadores["pozo"].sum()

    st.metric("💰 Jackpot acumulado", f"${jackpot:,.0f}")

    st.divider()

    st.subheader("Resumen por partido")

    st.dataframe(
        df.sort_values(by="fecha", ascending=False),
        use_container_width=True
    )