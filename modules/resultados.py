import streamlit as st
import pandas as pd
from zoneinfo import ZoneInfo
from utils.dataframe_utils import safe_int
from utils.dataframe_utils import asegurar_columnas
from database.google_sheets import connect
from utils.helpers import generar_id
from utils.data_loader import cargar_todo
from utils.flags import bandera as url_bandera


def resultados_page():

    # =========================
    # PERMISOS
    # =========================

    if st.session_state.get("rol") != "admin":

        st.error("No tienes permisos")

        st.stop()

    st.title("Registrar resultados reales")

    # =========================
    # CSS INPUTS
    # =========================

    st.markdown("""
    <style>

    div[data-testid="stTextInput"] input {
        text-align: center !important;
        font-size: 22px !important;
        font-weight: 700 !important;
    }

    </style>
    """, unsafe_allow_html=True)

    # =========================
    # CARGA DATOS
    # =========================

    data = cargar_todo()

    df_partidos = data["partidos"].copy()

    TZ = ZoneInfo("America/Bogota")

    ahora = pd.Timestamp.now(tz=TZ)

    df_partidos["fecha_hora"] = pd.to_datetime(
        df_partidos["fecha"].astype(str) + " " +
        df_partidos["hora"].astype(str),
        errors="coerce"
    )

    df_partidos["fecha_hora"] = (
        df_partidos["fecha_hora"]
        .dt.tz_localize("America/Bogota")
    )

    df_partidos["habilita_resultado"] = (
        df_partidos["fecha_hora"] +
        pd.Timedelta(hours=2)
    )

    df_result = data["resultados"].copy()

    df_result = asegurar_columnas(
        df_result,
        ["partido_id", "goles_local", "goles_visitante"]
    )

    # =========================
    # LIMPIEZA
    # =========================

    df_result["partido_id"] = (
        df_result["partido_id"]
        .astype(str)
        .str.strip()
    )

    df_result["goles_local"] = (
        df_result["goles_local"]
        .apply(safe_int)
    )

    df_result["goles_visitante"] = (
        df_result["goles_visitante"]
        .apply(safe_int)
    )

    # =========================
    # VALIDAR PARTIDOS
    # =========================

    if len(df_partidos) == 0:

        st.warning("No hay partidos")

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

    fecha_sel = st.date_input(
        "📅 Selecciona una fecha",
        value=pd.to_datetime(proxima_fecha).date(),
        min_value=pd.to_datetime(
            min(fechas_disponibles)
        ).date(),
        max_value=pd.to_datetime(
            max(fechas_disponibles)
        ).date()
    )

    # =========================
    # FILTRAR FECHA
    # =========================

    df_partidos = df_partidos[
        pd.to_datetime(df_partidos["fecha"]).dt.date
        == fecha_sel
    ]

    if len(df_partidos) == 0:

        st.warning("No hay partidos para esta fecha")

        return

    st.write("Seleccione los partidos a registrar")

    resultados = []

    # =========================
    # LOOP PARTIDOS
    # =========================

    for _, row in df_partidos.iterrows():

        puede_registrar_resultado = (
            ahora >= row["habilita_resultado"]
        )

        key_check = f"recalc_{row['id']}"

        key_local = f"res_local_{row['id']}"

        key_visit = f"res_visit_{row['id']}"

        resultado_existente = df_result[
            df_result["partido_id"]
            == str(row["id"])
        ]

        ya_registrado = (
            len(resultado_existente) > 0
        )

        # =========================
        # DEFAULTS
        # =========================

        if ya_registrado:

            recalcular_default = False

            goles_local_default = str(
                safe_int(
                    resultado_existente.iloc[0]["goles_local"]
                )
            )

            goles_visit_default = str(
                safe_int(
                    resultado_existente.iloc[0]["goles_visitante"]
                )
            )

        else:

            recalcular_default = True

            goles_local_default = "0"

            goles_visit_default = "0"

        # =========================
        # SESSION STATE
        # =========================

        if key_check not in st.session_state:

            st.session_state[key_check] = (
                recalcular_default
            )

        if key_local not in st.session_state:

            st.session_state[key_local] = (
                goles_local_default
            )

        if key_visit not in st.session_state:

            st.session_state[key_visit] = (
                goles_visit_default
            )

        # =========================
        # FLAGS
        # =========================

        codigo_local = url_bandera(
            row["equipo_local"]
        )

        codigo_visit = url_bandera(
            row["equipo_visitante"]
        )

        # =========================
        # CARD
        # =========================

        with st.container(border=True):

            # ─────────────────────
            # FECHA / HORA
            # ─────────────────────

            c_fecha, c_hora = st.columns(2)

            with c_fecha:

                st.caption(
                    f"📅 {row['fecha']}"
                )

            with c_hora:

                st.caption(
                    f"⏰ {row['hora']}"
                )

            # ─────────────────────
            # ESTADO
            # ─────────────────────

            if ya_registrado:

                st.warning("""
            ⚠️ Resultado ya registrado.
            """)

            else:

                if puede_registrar_resultado:

                    st.success(
                        "🟢 Registro habilitado"
                    )

                else:

                    restante = (
                        row["habilita_resultado"] - ahora
                    )

                    dias = restante.days

                    horas = restante.seconds // 3600

                    minutos = (
                        restante.seconds % 3600
                    ) // 60

                    if dias > 0:

                        st.warning(
                            f"⏳ Resultado habilitado en "
                            f"{dias}d {horas}h"
                        )

                    else:

                        st.warning(
                            f"⏳ Resultado habilitado en "
                            f"{horas}h {minutos}m"
                        )

            # ─────────────────────
            # CHECKBOX
            # ─────────────────────

            recalcular = st.checkbox(
                (
                    "Recalcular partido"
                    if ya_registrado
                    else "Registrar resultado"
                ),
                key=key_check,
                disabled=not puede_registrar_resultado
            )

            # ─────────────────────
            # LOCAL
            # ─────────────────────

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
                    label_visibility="collapsed",
                    max_chars=2,
                    disabled=(
                        not recalcular or
                        not puede_registrar_resultado
                    )
                )

            # ─────────────────────
            # VISITANTE
            # ─────────────────────

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
                    label_visibility="collapsed",
                    max_chars=2,
                    disabled=not recalcular
                )

            resultados.append({

                "partido_id": row["id"],

                "recalcular": recalcular,

                "goles_local": val_local,

                "goles_visitante": val_visit,

                "ya_registrado": ya_registrado

            })

            st.markdown(
                "<br>",
                unsafe_allow_html=True
            )

    st.divider()

    # =========================
    # GUARDAR
    # =========================

    if st.button(
        "Guardar resultados",
        disabled=not any(
            ahora >= p
            for p in df_partidos[
                "habilita_resultado"
            ]
        )
    ):

        # =========================
        # VALIDAR INPUTS
        # =========================

        for r in resultados:

            if not r["recalcular"]:

                continue

            for campo in [

                r["goles_local"],

                r["goles_visitante"]

            ]:

                if not campo.strip().isdigit():

                    st.error(
                        "Solo se permiten números enteros"
                    )

                    st.stop()

            gl = int(r["goles_local"].strip())

            gv = int(r["goles_visitante"].strip())

            if gl > 20 or gv > 20:

                st.error(
                    "No puedes ingresar un marcador mayor a 20"
                )

                st.stop()

        # =========================
        # CONEXIÓN
        # =========================

        try:

            db = connect()

        except Exception:

            st.error(
                "Error de conexión con Google Sheets"
            )

            return

        sheet = db.worksheet("resultados")

        resultados_existentes = (
            sheet.get_all_records()
        )

        guardados = 0

        # =========================
        # LOOP GUARDAR
        # =========================

        for r in resultados:

            if not r["recalcular"]:

                continue

            partido_df = df_partidos[
                df_partidos["id"]
                == r["partido_id"]
            ]

            if len(partido_df) == 0:

                continue

            partido = partido_df.iloc[0]

            # 🔒 BLOQUEAR SI YA LIQUIDADO

            if partido.get("estado") == "liquidado":

                st.warning(
                    f"Partido {r['partido_id']} ya fue liquidado"
                )

                continue

            fila_existente = None

            for i, p in enumerate(
                resultados_existentes
            ):

                if str(
                    p["partido_id"]
                ) == str(r["partido_id"]):

                    fila_existente = i + 2

                    break

            gl = int(
                r["goles_local"].strip()
            )

            gv = int(
                r["goles_visitante"].strip()
            )

            # =====================
            # UPDATE
            # =====================

            if fila_existente:

                sheet.update(
                    f"C{fila_existente}:D{fila_existente}",
                    [[gl, gv]]
                )

            # =====================
            # INSERT
            # =====================

            else:

                sheet.append_row([

                    generar_id(),

                    r["partido_id"],

                    gl,

                    gv

                ])

            guardados += 1

            # =====================
            # MARCAR LIQUIDADO
            # =====================

            sheet_partidos = db.worksheet(
                "partidos"
            )

            fila_partido = df_partidos[
                df_partidos["id"]
                == r["partido_id"]
            ].index[0] + 2

            sheet_partidos.update(
                f"I{fila_partido}",
                [["liquidado"]]
            )

        cargar_todo.clear()

        st.success(
            f"{guardados} resultados guardados"
        )