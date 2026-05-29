"""
Este módulo se encarga EXCLUSIVAMENTE de la liquidación
financiera y cálculo de resultados de partidos ya registrados.

Funciones principales:
- Detectar partidos con resultados oficiales registrados
- Liquidar premios y apuestas por partido
- Generar movimientos financieros
- Calcular jackpot y comisiones
- Actualizar puntos y rankings
- Permitir reliquidación controlada durante 10 minutos
- Evitar doble liquidación de partidos ya procesados

Importante:
Este módulo NO registra marcadores manualmente.
Solo procesa partidos previamente registrados
en resultados.py
"""

import streamlit as st
import pandas as pd
from zoneinfo import ZoneInfo   
from utils.data_loader import cargar_todo
from utils.dataframe_utils import safe_int
from utils.config import valor_apuesta_por_fase, porcentaje_admin
from utils.movimientos import registrar_movimientos
from utils.validaciones import apuesta_abierta


def _icono_resultado(pred_local, pred_visit, real_l, real_v):
    """Clasifica el pronóstico de un usuario vs el resultado real."""
    if pred_local == real_l and pred_visit == real_v:
        return "🎯 Exacto"
    diff_real = real_l - real_v
    diff_pred = pred_local - pred_visit
    if diff_real == 0 and diff_pred == 0:
        return "✅ Empate"
    if diff_real != 0 and diff_pred != 0 and (diff_real > 0) == (diff_pred > 0):
        return "✅ Ganador"
    return "❌ Fallo"


def resultados_partido_page():

    st.title("Resultados por partido")

    data = cargar_todo()

    TZ = ZoneInfo("America/Bogota")
    ahora = pd.Timestamp.now(tz=TZ)

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

    hay_resultados = len(df_res) > 0

    tabla = []  # siempre inicializar antes del bloque condicional

    if not hay_resultados:
        st.info("Aún no hay resultados registrados")

    # =========================
    # LIMPIEZA
    # =========================

    if hay_resultados:
        df_res["goles_local"]     = df_res["goles_local"].apply(safe_int)
        df_res["goles_visitante"] = df_res["goles_visitante"].apply(safe_int)

    # =========================
    # JOIN PARTIDOS
    # =========================

    if hay_resultados:

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

        # cargar config una sola vez antes del loop para evitar N llamadas repetidas
        from utils.config import obtener_config
        config_cache = obtener_config()

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

            valor = valor_apuesta_por_fase(fase, config=config_cache)

            if valor <= 0:
                valor = 5000

            pozo_bruto = participantes * valor
            comision   = round(pozo_bruto * porcentaje_admin(config=config_cache), 2)
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

            puede_reliquidar = False

            if liquidado:

                mov_liq = df_mov[
                    (df_mov["referencia"].astype(str) == ref) &
                    (df_mov["tipo"] == "comision")
                ]

                if not mov_liq.empty:

                    fecha_liq = mov_liq.iloc[0].get(
                        "fecha_liquidacion"
                    )

                    if pd.notna(fecha_liq):

                        fecha_liq = pd.Timestamp(fecha_liq)

                        if fecha_liq.tzinfo is None:

                            fecha_liq = fecha_liq.tz_localize(
                                "America/Bogota"
                            )

                        limite = fecha_liq + pd.Timedelta(minutes=10)

                        puede_reliquidar = ahora <= limite

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
                "puede_reliquidar": puede_reliquidar,
                "liquidado": liquidado
            })

        if len(tabla) == 0:
            st.warning("No hay partidos con participantes")

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

                if row["puede_reliquidar"]:

                    c2.warning("🟡 Editable")

                else:

                    c2.success("🔒 Final")

            if c2.button(
                "🔄 Reliquidar" if row["liquidado"] else "✅ Liquidar",
                key=row["partido_id"],
                disabled=(
                    row["liquidado"] and
                    not row["puede_reliquidar"]
                )
                ):

                    ref = f"partido_{row['partido_id']}"

                    # =========================
                    # PARTIDO
                    # =========================

                    partido_id = row["partido_id"]

                    df_pred_part = df_pred[
                        df_pred["partido_id"].astype(str) == str(partido_id)
                    ].copy()

                    # =========================
                    # RECALCULAR GANADORES DEL PARTIDO QUE SE ESTÁ LIQUIDANDO
                    # (no usar la variable del loop de construcción de tabla,
                    #  que puede contener datos del último partido iterado)
                    # =========================

                    res_partido = df_res[
                        df_res["partido_id"].astype(str) == str(partido_id)
                    ]

                    if not res_partido.empty:
                        real_local_liq  = safe_int(res_partido.iloc[0]["goles_local"])
                        real_visit_liq  = safe_int(res_partido.iloc[0]["goles_visitante"])
                    else:
                        real_local_liq  = row["resultado"].split("-")[0]
                        real_visit_liq  = row["resultado"].split("-")[1]
                        real_local_liq  = safe_int(real_local_liq)
                        real_visit_liq  = safe_int(real_visit_liq)

                    df_pred_part["goles_local"]     = df_pred_part["goles_local"].apply(safe_int)
                    df_pred_part["goles_visitante"] = df_pred_part["goles_visitante"].apply(safe_int)

                    ganadores_liq = df_pred_part[
                        (df_pred_part["goles_local"]     == real_local_liq) &
                        (df_pred_part["goles_visitante"] == real_visit_liq)
                    ]

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
                        "monto": row["comision"],
                        "fecha_liquidacion": str(ahora)
                    })

                    # PREMIOS

                    if row["ganadores"] > 0:

                        premio = row["premio"]

                        for _, g in ganadores_liq.iterrows():

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

    # =========================
    # FOTO DE APUESTAS
    # Sección independiente: muestra pronósticos de todos los
    # partidos cerrados, visible para admin y usuarios
    # =========================

    st.divider()
    st.subheader("📸 Foto de apuestas por partido")
    st.caption("Registro congelado de pronósticos al cierre de cada partido")

    partidos_cerrados = df_part[
        ~df_part.apply(
            lambda p: apuesta_abierta(p.get("fecha"), p.get("hora")),
            axis=1
        )
    ].copy()

    if partidos_cerrados.empty:
        st.info("Aún no hay partidos cerrados")
    else:
        for _, partido_row in partidos_cerrados.iterrows():

            pid = str(partido_row.get("id", ""))
            nombre_partido = (
                f"{partido_row.get('equipo_local', '')} vs {partido_row.get('equipo_visitante', '')}"
            )

            df_pred_foto = df_pred[
                df_pred["partido_id"].astype(str) == pid
            ].copy()

            if df_pred_foto.empty:
                continue

            df_pred_foto["goles_local"]     = df_pred_foto["goles_local"].apply(safe_int)
            df_pred_foto["goles_visitante"] = df_pred_foto["goles_visitante"].apply(safe_int)

            df_pred_foto["pronóstico"] = (
                df_pred_foto["goles_local"].astype(str)
                + " - "
                + df_pred_foto["goles_visitante"].astype(str)
            )

            # Verificar si hay resultado oficial registrado
            df_res_foto = df_res[df_res["partido_id"].astype(str) == pid] if "partido_id" in df_res.columns else pd.DataFrame()

            resultado_disponible = False
            real_l, real_v = 0, 0

            if not df_res_foto.empty:
                real_l = safe_int(df_res_foto.iloc[0].get("goles_local", 0))
                real_v = safe_int(df_res_foto.iloc[0].get("goles_visitante", 0))
                resultado_disponible = True

            if resultado_disponible:
                df_pred_foto["acierto"] = df_pred_foto.apply(
                    lambda r: _icono_resultado(
                        r["goles_local"], r["goles_visitante"], real_l, real_v
                    ),
                    axis=1
                )
                titulo = f"⚽ {nombre_partido}  —  Resultado: **{real_l}-{real_v}**"
                cols = ["usuario_id", "pronóstico", "acierto"]
            else:
                titulo = f"⚽ {nombre_partido}  —  Resultado pendiente"
                cols = ["usuario_id", "pronóstico"]

            with st.expander(titulo, expanded=False):
                st.dataframe(
                    df_pred_foto[cols].sort_values("usuario_id"),
                    hide_index=True,
                    use_container_width=True
                )
                st.caption(
                    f"📸 {len(df_pred_foto)} pronóstico(s) registrado(s) al cierre"
                )