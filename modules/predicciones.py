import streamlit as st
import pandas as pd
from utils.validaciones import apuesta_abierta, validar_marcador
from utils.saldos import saldo_usuario
from utils.flags import bandera as url_bandera
from utils.data_loader import cargar_todo
from utils.config import (
    valor_apuesta_por_fase,
    porcentaje_admin
)
from database.queries import (
    guardar_prediccion,
    eliminar_prediccion
)


def safe_int(value):
    if value is None:
        return 0
    try:
        return int(float(value))
    except:
        return 0


def predicciones_page():

    st.title("Registrar predicciones")

    st.markdown("""
    <style>
    /* Campo de goles: centrado, grande, sin decoraciones */
    div[data-testid="stTextInput"] input {
        text-align: center !important;
        font-size: 22px !important;
        font-weight: 700 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    usuario_actual = st.session_state.get("usuario")

    if not usuario_actual:
        st.error("Sesión no válida")
        st.stop()

    data = cargar_todo()

    df_partidos = data["partidos"].copy()
    #st.write(df_partidos.dtypes)
    df_partidos = df_partidos[df_partidos["estado"] == "programado"]

    df_pred = data["predicciones"].copy()

    saldo = saldo_usuario(usuario_actual)

    if saldo < 0:
        st.error(f"Saldo: ${saldo:,.0f}")
    else:
        st.success(f"Saldo: ${saldo:,.0f}")

    if len(df_partidos) == 0:
        st.warning("No hay partidos disponibles")
        return

    if len(df_pred) > 0:
        df_pred = df_pred[df_pred["usuario_id"] == usuario_actual]
    else:
        df_pred = pd.DataFrame(columns=[
            "usuario_id", "partido_id", "goles_local", "goles_visitante"
        ])

    # =========================
    # TIMEZONE
    # =========================

    #tz = pytz.timezone("America/Bogota")

    TZ = "America/Bogota"
    # tz_convert(None) produce un timestamp naive en hora Bogotá
    #ahora = pd.Timestamp.now(tz).tz_convert(None)

    ahora = pd.Timestamp.now(tz=TZ)
    #st.write("Ahora:", ahora)
    #st.write("Timezone:", ahora.tz)

    # =========================
    # FECHA COMPLETA PARTIDO
    # =========================

    #df_partidos["fecha_hora"] = pd.to_datetime(
     #   df_partidos["fecha"].astype(str) + " " +
      #  df_partidos["hora"].astype(str),
       # errors="coerce"
    #)

    # forzar naive en todos los registros para evitar TypeError en la comparación
    #df_partidos["fecha_hora"] = df_partidos["fecha_hora"].dt.tz_localize(None)

    df_partidos["fecha_hora"] = pd.to_datetime(
        df_partidos["fecha"].astype(str) + " " +
        df_partidos["hora"].astype(str),
        errors="coerce"
    )

    # asignar timezone Bogotá
    df_partidos["fecha_hora"] = (
        df_partidos["fecha_hora"]
        .dt.tz_localize(TZ)
    )

    #st.write("Ahora:", ahora)
    #st.write("Timezone:", ahora.tz)

    df_partidos["horas_restantes"] = (
    df_partidos["fecha_hora"] - ahora
    ).dt.total_seconds() / 3600

    # =========================
    # FILTRO: futuros + cerrados no liquidados aún
    # Desaparecen solo cuando tienen comisión registrada (= liquidados)
    # =========================

    df_mov_pred = data.get("movimientos", pd.DataFrame()).copy()

    if not df_mov_pred.empty and "tipo" in df_mov_pred.columns:
        ids_liquidados = df_mov_pred[
            df_mov_pred["tipo"] == "comision"
        ]["referencia"].str.replace("partido_", "", regex=False).tolist()
    else:
        ids_liquidados = []

    df_partidos = df_partidos[
        (df_partidos["fecha_hora"] > ahora) |
        (~df_partidos["id"].astype(str).isin(ids_liquidados))
    ].copy()

    # =========================
    # VALIDAR DISPONIBLES
    # =========================

    if len(df_partidos) == 0:

        st.warning("No hay partidos disponibles")

        return

    # =========================
    # FECHAS DISPONIBLES
    # =========================

    fechas_disponibles = sorted(
        df_partidos["fecha"].unique()
    )

    # =========================
    # PRÓXIMA FECHA
    # =========================

    proxima_fecha = fechas_disponibles[0]

    # =========================
    # CALENDARIO
    # =========================

    st.info(
    "⏳ Los pronósticos se habilitan únicamente "
    "24 horas antes del inicio de cada partido."
    )
    
    fecha_sel = st.date_input(
        "📅 Selecciona una fecha",
        value=pd.to_datetime(proxima_fecha).date(),
        min_value=pd.to_datetime(proxima_fecha).date(),
        max_value=pd.to_datetime(
            max(fechas_disponibles)
        ).date()
    )

    # =========================
    # FILTRAR FECHA
    # =========================

    df_partidos = df_partidos[
        pd.to_datetime(df_partidos["fecha"]).dt.date == fecha_sel
    ]
    st.write("Seleccione los partidos en los que desea participar")

    resultados = []

    for _, row in df_partidos.iterrows():

        key_check = f"check_{row['id']}"
        key_local = f"local_{row['id']}"
        key_visit = f"visit_{row['id']}"

        pred_existente = df_pred[
            df_pred["partido_id"].astype(str) == str(row["id"])
        ]

        if len(pred_existente) > 0:
            participa_default   = True
            goles_local_default = str(safe_int(pred_existente.iloc[0]["goles_local"]))
            goles_visit_default = str(safe_int(pred_existente.iloc[0]["goles_visitante"]))
        else:
            participa_default   = False
            goles_local_default = "0"
            goles_visit_default = "0"

        if key_check not in st.session_state:
            st.session_state[key_check] = participa_default
        if key_local not in st.session_state:
            st.session_state[key_local] = goles_local_default
        if key_visit not in st.session_state:
            st.session_state[key_visit] = goles_visit_default

        abierto = apuesta_abierta(
            row["fecha"],
            row["hora"],
            row.get("estado", "programado")
        )

        horas_restantes = row["horas_restantes"]

        habilitado_24h = horas_restantes <= 24

        puede_apostar = abierto and habilitado_24h


        codigo_local = url_bandera(row["equipo_local"])
        codigo_visit = url_bandera(row["equipo_visitante"])

        # ── Cálculo pozo antes del container para que esté disponible en todo el bloque ──
        predicciones_partido = data["predicciones"].copy()

        if not predicciones_partido.empty and "partido_id" in predicciones_partido.columns:
            predicciones_partido = predicciones_partido[
                predicciones_partido["partido_id"].astype(str) == str(row["id"])
            ]
        else:
            predicciones_partido = pd.DataFrame()

        participantes = 0

        if not predicciones_partido.empty:
            if "participa" in predicciones_partido.columns:
                participantes = predicciones_partido[
                    predicciones_partido["participa"] == True
                ]["usuario_id"].nunique()
            elif "usuario_id" in predicciones_partido.columns:
                participantes = predicciones_partido["usuario_id"].nunique()

        valor_apuesta = valor_apuesta_por_fase(row["fase"])
        pozo_total = participantes * valor_apuesta
        premio_estimado = pozo_total * (1 - porcentaje_admin())

        with st.container(border=True):

            # ── Fecha y hora ──────────────────────────
            c_fecha, c_hora = st.columns(2)
            with c_fecha:
                st.caption(f"📅 {row['fecha']}")
            with c_hora:
                st.caption(f"⏰ {row['hora']}")

            


            # ── Estado ───────────────────────────────

            if not abierto:

                st.error("🔒 Partido iniciado")

                # Mostrar equipos
                c_local, c_vs, c_visit = st.columns([5, 1, 5])

                with c_local:
                    st.markdown(
                        f"""<div style="display:flex; align-items:center; gap:8px;">
                            <img src="{codigo_local}" style="width:26px; border-radius:2px;">
                            <span style="font-size:15px; font-weight:600;">{row['equipo_local']}</span>
                        </div>""",
                        unsafe_allow_html=True
                    )

                with c_vs:
                    st.markdown(
                        "<div style='text-align:center; padding-top:4px; font-weight:600;'>vs</div>",
                        unsafe_allow_html=True
                    )

                with c_visit:
                    st.markdown(
                        f"""<div style="display:flex; align-items:center; gap:8px;">
                            <img src="{codigo_visit}" style="width:26px; border-radius:2px;">
                            <span style="font-size:15px; font-weight:600;">{row['equipo_visitante']}</span>
                        </div>""",
                        unsafe_allow_html=True
                    )

                st.markdown("<br>", unsafe_allow_html=True)

                # Mostrar métricas del pozo aunque esté cerrado
                if participantes > 0:

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("👥 Participantes", participantes)

                    with col2:
                        st.metric("💰 Pozo", f"${pozo_total:,.0f}")

                    with col3:
                        st.metric("🏆 Premio Estimado", f"${premio_estimado:,.0f}")

                else:

                    st.caption("Sin participantes en este partido")

                st.markdown("<br>", unsafe_allow_html=True)
                continue

            elif puede_apostar:

                st.success("🟢 Pronósticos habilitados")

            else:

                tiempo_restante = row["fecha_hora"] - ahora

                dias = tiempo_restante.days
                horas = tiempo_restante.seconds // 3600
                minutos = (tiempo_restante.seconds % 3600) // 60

                if dias > 0:

                    st.warning(
                        f"⏳ Pronósticos disponibles en "
                        f"{dias}d {horas}h"
                    )

                else:

                    st.warning(
                        f"⏳ Pronósticos disponibles en "
                        f"{horas}h {minutos}m"
                    )

            # ── Participar ───────────────────────────
            participa = st.checkbox(
                "Participar",
                key=key_check,
                disabled=not puede_apostar
            )

            # ── MARCADOR ─────────────────────────────


            c_info_l, c_num_l = st.columns([3, 1])

            with c_info_l:
                st.markdown(
                    f"""
                    <div style="display:flex; align-items:center;
                                gap:8px; padding-top:8px;">
                        <img src="{codigo_local}"
                             style="width:26px; border-radius:2px; flex-shrink:0;">
                        <span style="font-size:15px; font-weight:600;">
                            {row['equipo_local']}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with c_num_l:
                val_local = st.text_input(
                    "Local",
                    key=key_local,
                    disabled=(not participa or not puede_apostar),
                    label_visibility="collapsed",
                    max_chars=2
                )



            c_info_v, c_num_v = st.columns([3, 1])

            with c_info_v:
                st.markdown(
                    f"""
                    <div style="display:flex; align-items:center;
                                gap:8px; padding-top:8px;">
                        <img src="{codigo_visit}"
                             style="width:26px; border-radius:2px; flex-shrink:0;">
                        <span style="font-size:15px; font-weight:600;">
                            {row['equipo_visitante']}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with c_num_v:
                val_visit = st.text_input(
                    "Visitante",
                    key=key_visit,
                    disabled=(not participa or not puede_apostar),
                    label_visibility="collapsed",
                    max_chars=2
                )
            # ── MINI PANEL DEL PARTIDO ─────────────────────

            st.caption(
                f"Comisión administrativa: "
                f"{porcentaje_admin()*100:.0f}%"
            )

            if participantes > 0:

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "👥 Participantes",
                        participantes
                    )

                with col2:
                    st.metric(
                        "💰 Pozo",
                        f"${pozo_total:,.0f}"
                    )

                with col3:
                    st.metric(
                        "🏆 Premio Estimado",
                        f"${premio_estimado:,.0f}"
                    )

            st.caption(
                f"Comisión administrativa: "
                f"{porcentaje_admin()*100:.0f}%"
            )

            resultados.append({
                "partido_id":      row["id"],
                "participa":       participa,
                "goles_local":     val_local,
                "goles_visitante": val_visit,
                "abierto":         abierto
            })

            st.markdown("<br>", unsafe_allow_html=True)

    st.divider()

    if st.button("Guardar predicciones"):

        # Validar marcadores
        for r in resultados:

            if not r["abierto"] or not r["participa"]:
                continue

            for campo in [r["goles_local"], r["goles_visitante"]]:

                if not campo.strip().isdigit():

                    st.error(
                        "Solo se permiten números enteros"
                    )
                    st.stop()

            gl = int(r["goles_local"])
            gv = int(r["goles_visitante"])

            if not validar_marcador(gl, gv):

                st.error(
                    "No puedes ingresar un marcador mayor a 20"
                )
                st.stop()

        guardados = 0
        eliminados = 0

        for r in resultados:

            if not r["abierto"]:
                continue

            if r["participa"]:

                guardar_prediccion(

                    usuario_id=usuario_actual,

                    partido_id=r["partido_id"],

                    goles_local=int(r["goles_local"]),

                    goles_visitante=int(r["goles_visitante"])

                )

                guardados += 1

            else:

                eliminado = eliminar_prediccion(

                    usuario_id=usuario_actual,

                    partido_id=r["partido_id"]

                )
                if eliminado:

                    eliminados += 1

        cargar_todo.clear()

        mensajes = []

        if guardados:
            mensajes.append(f"{guardados} guardadas")

        if eliminados:
            mensajes.append(f"{eliminados} eliminadas")

        if mensajes:

            st.success(" / ".join(mensajes))

        else:

            st.info("Sin cambios")