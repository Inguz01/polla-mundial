import streamlit as st
import pandas as pd
from utils.dataframe_utils import safe_int
from database.google_sheets import connect
from utils.helpers import generar_id
#from utils.premios import calcular_premio_partido
from utils.data_loader import cargar_todo

def resultados_page():

    # 🔒 CONTROL DE PERMISOS
    if st.session_state.get("rol") != "admin":
        st.error("No tienes permisos para acceder a esta sección")
        st.stop()

    st.title("Registrar resultados reales")


    # ===== carga centralizada =====

    data = cargar_todo()

    df_partidos = data["partidos"].copy()

    df_result = data["resultados"].copy()

    # 🔒 asegurar estructura SIEMPRE (aunque esté vacío)
    from utils.dataframe_utils import asegurar_columnas

    df_result = asegurar_columnas(
        df_result,
        ["partido_id", "goles_local", "goles_visitante"]
    )

    # 🔥 asegurar tipos correctos
    df_result["partido_id"] = df_result["partido_id"].astype(str)
    df_result["goles_local"] = df_result["goles_local"].apply(safe_int)
    df_result["goles_visitante"] = df_result["goles_visitante"].apply(safe_int)

    # ==============================


    if len(df_partidos) == 0:

        st.warning("No hay partidos")

        return


    fechas = sorted(df_partidos["fecha"].unique())


    fecha_sel = st.selectbox(

        "Seleccione fecha",

        fechas

    )


    df_partidos = df_partidos[

        df_partidos["fecha"] == fecha_sel

    ]


    resultados = []


    h1, h2 = st.columns([4,3])

    h1.write("Partido")

    h2.write("Resultado real")

    st.divider()

    st.subheader("Recalcular partido")

    # crear label 
    df_partidos["label"] = (
        df_partidos["equipo_local"] + " vs " +
        df_partidos["equipo_visitante"] +
        " (ID: " + df_partidos["id"].astype(str) + ")"
    )

    # mapa label → id
    mapa_partidos = dict(zip(df_partidos["label"], df_partidos["id"]))

    # select 
    label_sel = st.selectbox(
        "Selecciona partido a recalcular",
        list(mapa_partidos.keys())
    )

    # recuperar id real
    partido_recalc = mapa_partidos[label_sel]

    for _, row in df_partidos.iterrows():

        col_partido, col_score = st.columns([4,3])


        key_local = f"res_local_{row['id']}"

        key_visit = f"res_visit_{row['id']}"


        resultado_existente = df_result[

            df_result["partido_id"].astype(str)

            == str(row["id"])

        ]


        if len(resultado_existente) > 0:

            local_default = safe_int(

                resultado_existente.iloc[0]["goles_local"]

            )

            visit_default = safe_int(

                resultado_existente.iloc[0]["goles_visitante"]

            )

        else:

            local_default = 0

            visit_default = 0


        if key_local not in st.session_state:

            st.session_state[key_local] = local_default


        if key_visit not in st.session_state:

            st.session_state[key_visit] = visit_default


        with col_partido:

            st.write(

                f"{row['equipo_local']} vs {row['equipo_visitante']}"

            )


        with col_score:

            c1, c2, c3 = st.columns([1,0.3,1])


            with c1:

                goles_local = st.number_input(

                    " ",

                    min_value=0,

                    max_value=20,

                    step=1,

                    format="%d",

                    key=key_local

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

                    key=key_visit

                )


        resultados.append({

            "partido_id": row["id"],

            "goles_local": goles_local,

            "goles_visitante": goles_visitante

        })


    st.divider()



    if st.button("Guardar resultados"):

        try:
            db = connect()
        except Exception:
            st.error("Error de conexión con Google Sheets")

            return

        sheet = db.worksheet("resultados")

        resultados_existentes = sheet.get_all_records()


        guardados = 0


        for r in resultados:

            partido_df = df_partidos[df_partidos["id"] == r["partido_id"]]

            if len(partido_df) == 0:
                continue

            partido = partido_df.iloc[0]

            # 🔒 bloquear si ya está liquidado
            if partido.get("estado") == "liquidado":
                st.warning(f"Partido {r['partido_id']} ya fue liquidado")
                continue


            fila_existente = None


            for i, p in enumerate(resultados_existentes):

                if str(p["partido_id"]) == str(r["partido_id"]):

                    fila_existente = i + 2

                    break


            # actualizar resultado existente

            if fila_existente:


                sheet.update(

                    f"C{fila_existente}:D{fila_existente}",

                    [[

                        int(r["goles_local"]),

                        int(r["goles_visitante"])

                    ]]

                )

            


            # crear nuevo resultado

            else:


                sheet.append_row([

                    generar_id(),

                    r["partido_id"],

                    int(r["goles_local"]),

                    int(r["goles_visitante"])

                ])


            guardados += 1

            cargar_todo.clear()

            #resultado_financiero = calcular_premio_partido(r["partido_id"])

            # marcar partido como liquidado
            sheet_partidos = db.worksheet("partidos")

            fila_partido = df_partidos[
                df_partidos["id"] == r["partido_id"]
            ].index[0] + 2

            
            sheet_partidos.update(f"I{fila_partido}", [["liquidado"]])

        st.success(f"{guardados} resultados guardados")