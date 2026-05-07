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
    df_mov  = data.get("movimientos", pd.DataFrame()).copy()

    # =========================
    # NORMALIZAR MOVIMIENTOS
    # =========================

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

    # =========================
    # VALIDACIÓN
    # =========================

    if len(df_res) == 0:
        st.info("Aún no hay resultados registrados")
        return

    # =========================
    # LIMPIEZA
    # =========================

    df_res["goles_local"]     = df_res["goles_local"].apply(safe_int)
    df_res["goles_visitante"] = df_res["goles_visitante"].apply(safe_int)

    # =========================
    # JOIN PARTIDOS
    # =========================

    df_res = df_res.merge(
        df_part[["id", "equipo_local", "equipo_visitante", "fase"]],
        left_on="partido_id",
        right_on="id",
        how="left"
    )

    # =========================
    # TABLA GENERAL
    # =========================

    tabla = []

    df_res = df_res.sort_values(
        by="partido_id",
        ascending=False
    )

    for _, row in df_res.iterrows():

        partido_id = str(row["partido_id"])

        fase = row["fase"]

        real_local = safe_int(row["goles_local"])
        real_visit = safe_int(row["goles_visitante"])

        partido = f"{row['equipo_local']} vs {row['equipo_visitante']}"

        # =========================
        # PREDICCIONES
        # =========================

        df_pred_part = df_pred[
            df_pred["partido_id"].astype(str) == partido_id
        ].copy()

        participantes = len(df_pred_part)

        if participantes == 0:
            continue

        # =========================
        # POZO
        # =========================

        valor = valor_apuesta_por_fase(fase)

        if valor <= 0:
            valor = 5000

        pozo_bruto = participantes * valor
        comision   = round(pozo_bruto * porcentaje_admin(), 2)
        pozo       = round(pozo_bruto - comision, 2)

        # =========================
        # GANADORES
        # =========================

        df_pred_part["goles_local"] = df_pred_part["goles_local"].apply(safe_int)
        df_pred_part["goles_visitante"] = df_pred_part["goles_visitante"].apply(safe_int)

        ganadores = df_pred_part[
            (df_pred_part["goles_local"] == real_local) &
            (df_pred_part["goles_visitante"] == real_visit)
        ]

        num_ganadores = len(ganadores)

        premio = round(pozo / num_ganadores, 2) if num_ganadores > 0 else 0

        # =========================
        # LIQUIDADO
        # =========================

        ref = f"partido_{partido_id}"

        liquidado = not df_mov[
            (df_mov["referencia"].astype(str) == ref) &
            (df_mov["tipo"] == "comision")
        ].empty

        tabla.append({
            "partido_id": partido_id,
            "partido": partido,
            "resultado": f"{real_local}-{real_visit}",
            "participantes": participantes,
            "valor": valor,
            "pozo_bruto": pozo_bruto,
            "comision": comision,
            "ganadores": num_ganadores,
            "premio": premio,
            "jackpot": pozo if num_ganadores == 0 else 0,
            "liquidado": liquidado
        })

    if len(tabla) == 0:
        st.warning("No hay partidos con participantes")
        return

    # =========================
    # DISPLAY
    # =========================

    for row in tabla:

        c1, c2 = st.columns([8, 2])

        c1.write(
            f"""
            ⚽ **{row['partido']}**  
            Resultado: **{row['resultado']}** | 
            Participantes: **{row['participantes']}** | 
            Valor apuesta: **${row['valor']:,.0f}** | 
            Pozo: **${row['pozo_bruto']:,.0f}** | 
            Comisión: **${row['comision']:,.0f}** | 
            Ganadores: **{row['ganadores']}** | 
            Premio c/u: **${row['premio']:,.0f}** |
            Jackpot: **${row['jackpot']:,.0f}**
            """
        )

        # =========================
        # ADMIN
        # =========================

        if st.session_state.get("rol") == "admin":

            if row["liquidado"]:

                c2.success("Liquidado")

            else:

                if c2.button("Liquidar", key=row["partido_id"]):

                    ref = f"partido_{row['partido_id']}"

                    # =========================
                    # PARTIDO
                    # =========================

                    partido_id = row["partido_id"]

                    df_pred_part = df_pred[
                        df_pred["partido_id"].astype(str) == str(partido_id)
                    ].copy()

                    # =========================
                    # REVERSAR TODO
                    # =========================

                    df_mov_partido = df_mov[
                        df_mov["referencia"].astype(str) == ref
                    ]

                    reversos = []

                    if not df_mov_partido.empty:

                        for _, mov in df_mov_partido.iterrows():

                            reversos.append({
                                "usuario_id": mov["usuario_id"],
                                "tipo": "reverso",
                                "referencia": ref,
                                "monto": -float(mov["monto"])
                            })

                        registrar_movimientos(reversos)

                    # =========================
                    # NUEVA LIQUIDACIÓN
                    # =========================

                    movimientos = []

                    # REGISTRAR APUESTAS SOLO SI NO EXISTEN
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
                                "monto": -row["valor"]
                            })

                    # COMISIÓN

                    movimientos.append({
                        "usuario_id": "admin",
                        "tipo": "comision",
                        "referencia": ref,
                        "monto": row["comision"]
                    })

                    # PREMIOS

                    if row["ganadores"] > 0:

                        premio = row["premio"]

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
                            "monto": row["pozo_bruto"] - row["comision"]
                        })

                    # GUARDAR

                    if movimientos:
                        registrar_movimientos(movimientos)

                    cargar_todo.clear()

                    st.success("✅ Partido liquidado correctamente")

                    st.rerun()

        st.divider()