import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from utils.saldos import saldo_usuario
from database.google_sheets import connect
from utils.helpers import generar_id
from utils.movimientos import registrar_movimiento
from utils.config import valor_apuesta_por_fase
from utils.data_loader import cargar_todo


USUARIO_ACTUAL = "usuario_demo"


def safe_int(value):

    if value is None:
        return 0

    try:
        return int(float(value))
    except:
        return 0


def partido_abierto(fecha, hora):

    try:

        fecha_hora = datetime.strptime(
            f"{fecha} {hora}",
            "%Y-%m-%d %H:%M"
        )

        limite = fecha_hora - timedelta(minutes=5)

        return datetime.now() < limite

    except:

        return True



def predicciones_page():

    st.title("Registrar predicciones")

    # ========= CARGA CENTRALIZADA =========

    data = cargar_todo()

    df_partidos = data["partidos"].copy()

    df_pred = data["predicciones"].copy()

    df_equipos = data["equipos"].copy()

    mapa_codigos = dict(
        zip(
            df_equipos["equipo"].str.strip(),
            df_equipos["codigo"].str.strip()
        )
    )
    
    
    # ======================================


    saldo = saldo_usuario(USUARIO_ACTUAL)

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

            df_pred["usuario_id"] == USUARIO_ACTUAL

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


        abierto = partido_abierto(

            row["fecha"],

            row["hora"]

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

            partido = df_partidos[df_partidos["id"] == r["partido_id"]].iloc[0]
            fase = partido["fase"]

            fila_existente = None


            for i, p in enumerate(predicciones_existentes):

                if (

                    p["usuario_id"] == USUARIO_ACTUAL

                    and str(p["partido_id"]) == str(r["partido_id"])

                ):

                    fila_existente = i + 2

                    break


            # ========= PARTICIPA =========

            if r["participa"] and r["abierto"]:


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

                        USUARIO_ACTUAL,

                        r["partido_id"],

                        int(r["goles_local"]),

                        int(r["goles_visitante"]),

                        1,

                        0

                    ])


                    registrar_movimiento(

                        USUARIO_ACTUAL,

                        "apuesta",

                        f"partido_{r['partido_id']}",

                        -valor_apuesta_por_fase(fase)

                    )


                guardados += 1


            # ========= NO PARTICIPA =========

            elif not r["participa"] and fila_existente:


                pred_sheet.delete_rows(fila_existente)


                registrar_movimiento(

                    USUARIO_ACTUAL,

                    "ajuste_apuesta",

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