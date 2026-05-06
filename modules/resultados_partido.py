import streamlit as st
import pandas as pd

from utils.data_loader import cargar_todo
from utils.dataframe_utils import safe_int
from utils.config import valor_apuesta_por_fase, porcentaje_admin
from utils.movimientos import registrar_movimientos


def resultados_partido_page():

    st.title("Resultados por partido")

    data = cargar_todo()

    df_pred = data["predicciones"].copy()
    df_res  = data["resultados"].copy()
    df_part = data["partidos"].copy()
    df_mov = data.get("movimientos", pd.DataFrame()).copy()

    if df_mov is None or df_mov.empty:
        df_mov = pd.DataFrame(columns=[
            "usuario_id",
            "tipo",
            "referencia",
            "monto"
        ])

    if "usuario_id" not in df_mov.columns and "usuario" in df_mov.columns:
        df_mov["usuario_id"] = df_mov["usuario"]

    if "referencia" not in df_mov.columns:
        df_mov["referencia"] = None

    if len(df_res) == 0:
        st.info("Aún no hay resultados registrados")
        return

    # =========================
    # LIMPIEZA
    # =========================

    df_res["goles_local"]     = df_res["goles_local"].apply(safe_int)
    df_res["goles_visitante"] = df_res["goles_visitante"].apply(safe_int)

    # =========================
    # SELECTOR DE PARTIDO
    # =========================

    df_res = df_res.merge(
        df_part[["id", "equipo_local", "equipo_visitante", "fase"]],
        left_on="partido_id",
        right_on="id",
        how="left"
    )

    df_res["partido"] = (
        df_res["equipo_local"] + " vs " + df_res["equipo_visitante"]
    )

    partido_sel = st.selectbox(
        "Selecciona un partido",
        df_res["partido"].unique()
    )

    row_partido = df_res[df_res["partido"] == partido_sel].iloc[0]

    partido_id  = str(row_partido["partido_id"])
    fase        = row_partido["fase"]
    real_local  = row_partido["goles_local"]
    real_visit  = row_partido["goles_visitante"]

    # =========================
    # RESULTADO
    # =========================

    st.subheader(partido_sel)
    st.write(f"Resultado real: **{real_local} - {real_visit}**")

    # =========================
    # APUESTAS DEL PARTIDO
    # =========================

    df_pred_part = df_pred[
        df_pred["partido_id"].astype(str) == partido_id
    ].copy()

    participantes = len(df_pred_part)

    if participantes == 0:
        st.warning("No hubo participantes en este partido")
        return

    # =========================
    # POZO
    # =========================

    valor = valor_apuesta_por_fase(fase)

    if valor <= 0:
        valor = 5000
        st.warning(f"⚠️ Valor por defecto aplicado: $5.000")

    pozo_bruto = participantes * valor
    comision   = round(pozo_bruto * porcentaje_admin(), 2)
    pozo       = round(pozo_bruto - comision, 2)

    st.divider()
    st.write(f"Participantes: **{participantes}**")
    st.write(f"Valor apuesta: **${valor:,.0f}**")
    st.write(f"Pozo bruto: **${pozo_bruto:,.0f}**")
    st.write(f"Comisión: **${comision:,.0f}**")
    st.write(f"Pozo: **${pozo:,.0f}**")

    # =========================
    # GANADORES
    # =========================

    df_pred_part["goles_local"]     = df_pred_part["goles_local"].apply(safe_int)
    df_pred_part["goles_visitante"] = df_pred_part["goles_visitante"].apply(safe_int)

    ganadores = df_pred_part[
        (df_pred_part["goles_local"] == real_local) &
        (df_pred_part["goles_visitante"] == real_visit)
    ]

    st.divider()

    if len(ganadores) > 0:
        premio = round(pozo / len(ganadores), 2)
        st.success(f"{len(ganadores)} ganador(es) — ${premio:,.0f} c/u")
    else:
        st.warning("Sin ganadores — va a jackpot")

    # =========================
    # BOTÓN LIQUIDAR
    # =========================

    if st.session_state.get("rol") == "admin":

        if st.button("Liquidar partido"):

            ref = f"partido_{partido_id}"

            df_mov_partido = df_mov[
                df_mov["referencia"].astype(str) == ref
            ]

            # =========================
            # REVERSOS (solo financieros)
            # =========================

            reversos = []

            if not df_mov_partido.empty:

                for _, mov in df_mov_partido.iterrows():

                    if mov["tipo"] not in ["premio", "comision", "jackpot_pago"]:
                        continue

                    reversos.append({
                        "usuario_id": mov["usuario_id"],
                        "tipo": "reverso",
                        "referencia": ref,
                        "monto": -float(mov["monto"])
                    })

            if reversos:
                registrar_movimientos(reversos)

            # =========================
            # NUEVA LIQUIDACIÓN
            # =========================

            movimientos = []

            # REGISTRAR APUESTAS
            apuestas_existentes = df_mov[
                (df_mov["referencia"].astype(str) == ref) &
                (df_mov["tipo"] == "apuesta")
            ]

            if apuestas_existentes.empty:
                for _, p in df_pred_part.iterrows():
                    movimientos.append({
                        "usuario_id": p["usuario_id"],
                        "tipo": "apuesta",
                        "referencia": ref,
                        "monto": -valor
                    })

            # COMISIÓN
            movimientos.append({
                "usuario_id": "admin",
                "tipo": "comision",
                "referencia": ref,
                "monto": comision
            })

            # 🏆 PREMIOS
            if len(ganadores) > 0:

                premio = round(pozo / len(ganadores), 2)

                for _, g in ganadores.iterrows():
                    movimientos.append({
                        "usuario_id": g["usuario_id"],
                        "tipo": "premio",
                        "referencia": ref,
                        "monto": premio
                    })

            else:
                movimientos.append({
                    "usuario_id": "sistema",
                    "tipo": "jackpot_aporte",
                    "referencia": ref,
                    "monto": pozo
                })

            if movimientos:
                registrar_movimientos(movimientos)

            cargar_todo.clear()
            st.success("✅ Liquidación procesada correctamente")
            st.rerun()

    else:
        st.info("Solo el administrador puede liquidar partidos")