import streamlit as st
import pandas as pd

from utils.validaciones import apuesta_abierta, validar_marcador
from utils.saldos import saldo_usuario
from database.google_sheets import connect
from utils.helpers import generar_id
from utils.movimientos import registrar_movimiento
from utils.config import valor_apuesta_por_fase
from utils.data_loader import cargar_todo

def safe_int(value):

    if value is None:
        return 0

    try:
        return int(float(value))
    except:
        return 0

def predicciones_page():

    st.title("Registrar predicciones")

    # ========= CARGA CENTRALIZADA =========

    usuario_actual = st.session_state.get("usuario")

    if not usuario_actual:
        st.error("Sesión no válida")
        st.stop()
        
    data = cargar_todo()

    df_partidos = data["partidos"].copy()

    df_partidos = df_partidos[
    df_partidos["estado"] == "programado"
]

    df_pred = data["predicciones"].copy()

    df_equipos = data["equipos"].copy()

    mapa_codigos = dict(
        zip(
            df_equipos["equipo"].str.strip(),
            df_equipos["codigo"].str.strip()
        )
    )

        # 🔒 BLOQUEAR ADMIN
    if st.session_state.get("rol") == "admin":
        st.warning("Los administradores no pueden realizar predicciones")
        st.stop()
    
    
    # ======================================


    saldo = saldo_usuario(usuario_actual)

    if saldo < 0:

        st.error(f"Saldo: ${saldo:,.0f}")

    else:

        st.success(f"Saldo: ${saldo:,.0f}")


    if len(df_partidos) == 0:

        st.warning("No hay partidos disponibles")

        return


    # predicciones del usuario

    if len(df_pred) > 0:

        df_pred = df_pred[

            df_pred["usuario_id"] == usuario_actual

        ]

    else:

        df_pred = pd.DataFrame(columns=[

            "usuario_id",
            "partido_id",
            "goles_local",
            "goles_visitante"

        ])


    fechas = sorted(df_partidos["fecha"].unique())


    fecha_sel = st.selectbox(

        "Seleccione fecha",

        fechas

    )


    df_partidos = df_partidos[

        df_partidos["fecha"] == fecha_sel

    ]


    st.write("Seleccione los partidos en los que desea participar")


    resultados = []


    h1, h2, h3 = st.columns([1,4,3])

    h1.write("✔")

    h2.write("Partido")

    h3.write("Marcador")

    st.divider()



    for _, row in df_partidos.iterrows():

        col_check, col_partido, col_score = st.columns([1,4,3])


        key_check = f"check_{row['id']}"

        key_local = f"local_{row['id']}"

        key_visit = f"visit_{row['id']}"


        pred_existente = df_pred[

            df_pred["partido_id"].astype(str)
            == str(row["id"])

        ]


        if len(pred_existente) > 0:

            participa_default = True

            goles_local_default = safe_int(

                pred_existente.iloc[0]["goles_local"]

            )

            goles_visit_default = safe_int(

                pred_existente.iloc[0]["goles_visitante"]

            )

        else:

            participa_default = False

            goles_local_default = 0

            goles_visit_default = 0


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


        with col_check:

            participa = st.checkbox(

                "",

                key=key_check,

                disabled=not abierto

            )


        with col_partido:

            codigo_local = mapa_codigos.get(row["equipo_local"].strip(), "xx")
            codigo_visit = mapa_codigos.get(row["equipo_visitante"].strip(), "xx")

            col_a, col_b, col_c = st.columns([1,4,1])

            with col_a:
                st.image(f"https://flagcdn.com/w40/{codigo_local}.png", width=30)

            with col_b:
                st.write(f"{row['equipo_local']} vs {row['equipo_visitante']}")

            with col_c:
                st.image(f"https://flagcdn.com/w40/{codigo_visit}.png", width=30)


        with col_score:

            c1, c2, c3 = st.columns([1,0.3,1])


            with c1:

                goles_local = st.number_input(

                    " ",

                    min_value=0,

                    max_value=20,

                    step=1,

                    format="%d",

                    key=key_local,

                    disabled=(not participa or not abierto)

                )


            with c2:

                st.markdown(

                    "<div style='text-align:center;margin-top:8px'>-</div>",

                    unsafe_allow_html=True

                )


            with c3:

                goles_visitante = st.number_input(

                    " ",

                    min_value=0,

                    max_value=20,

                    step=1,

                    format="%d",

                    key=key_visit,

                    disabled=(not participa or not abierto)

                )


        resultados.append({

            "partido_id": row["id"],

            "participa": participa,

            "goles_local": goles_local,

            "goles_visitante": goles_visitante,

            "abierto": abierto

        })


    st.divider()


    if st.button("Guardar predicciones"):


        db = connect()

        pred_sheet = db.worksheet("predicciones")

        predicciones_existentes = pred_sheet.get_all_records()


        guardados = 0

        eliminados = 0


        for r in resultados:

            # 🔒 bloquear si partido cerrado
            if not r["abierto"]:
                continue

            # 🔒 validar marcador
            if r["participa"]:
                if not validar_marcador(r["goles_local"], r["goles_visitante"]):
                    st.error("Marcador inválido")
                    st.stop()

            # 🔒 obtener partido seguro
            partido_df = df_partidos[df_partidos["id"] == r["partido_id"]]

            if len(partido_df) == 0:
                continue

            partido = partido_df.iloc[0]
            fase = partido["fase"]

            fila_existente = None

            for i, p in enumerate(predicciones_existentes):

                if (
                    p["usuario_id"] == usuario_actual
                    and str(p["partido_id"]) == str(r["partido_id"])
                ):
                    fila_existente = i + 2
                    break

            # ========= PARTICIPA =========
            if r["participa"]:

                if fila_existente:

                    pred_sheet.update(
                        f"D{fila_existente}:G{fila_existente}",
                        [[
                            int(r["goles_local"]),
                            int(r["goles_visitante"]),
                            1,
                            0
                        ]]
                    )

                else:

                    pred_sheet.append_row([
                        generar_id(),
                        usuario_actual,
                        r["partido_id"],
                        int(r["goles_local"]),
                        int(r["goles_visitante"]),
                        1,
                        0
                    ])

                    data = cargar_todo()
                    df_mov = data.get("movimientos", pd.DataFrame())

                    # =========================
                    # NORMALIZAR MOVIMIENTOS
                    # =========================

                    # si viene vacío o None
                    if df_mov is None or df_mov.empty:
                        df_mov = pd.DataFrame(columns=[
                            "usuario_id",
                            "tipo",
                            "referencia",
                            "monto"
                        ])

                    # asegurar columnas mínimas
                    for col in ["usuario_id", "tipo", "referencia"]:
                        if col not in df_mov.columns:
                            df_mov[col] = None

                    # compatibilidad con versiones viejas (usuario vs usuario_id)
                    if "usuario_id" not in df_mov.columns and "usuario" in df_mov.columns:
                        df_mov["usuario_id"] = df_mov["usuario"]

                    # evitar errores de tipo
                    df_mov["usuario_id"] = df_mov["usuario_id"].astype(str)
                    df_mov["referencia"] = df_mov["referencia"].astype(str)
                        
                    ya_pago = df_mov[
                        (df_mov["usuario_id"] == usuario_actual) &
                        (df_mov["referencia"] == f"partido_{r['partido_id']}") &
                        (df_mov["tipo"] == "apuesta")
                    ]

                    if len(ya_pago) == 0:

                        registrar_movimiento(
                            usuario_actual,
                            "apuesta",
                            f"partido_{r['partido_id']}",
                            -valor_apuesta_por_fase(fase)
                        )

                guardados += 1

            # ========= NO PARTICIPA =========
            elif fila_existente:

                pred_sheet.delete_rows(fila_existente)

                registrar_movimiento(
                    usuario_actual,
                    "reverso_apuesta",
                    f"partido_{r['partido_id']}",
                    valor_apuesta_por_fase(fase)
                )

                eliminados += 1


        # refrescar cache global

        cargar_todo.clear()


        mensajes = []


        if guardados > 0:

            mensajes.append(f"{guardados} guardadas")


        if eliminados > 0:

            mensajes.append(f"{eliminados} eliminadas")


        if len(mensajes) > 0:

            st.success(" / ".join(mensajes))

        else:

            st.info("Sin cambios")