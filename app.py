import streamlit as st

# =============================
# CONFIGURACIÓN INICIAL
# =============================

st.set_page_config(
    page_title="Polla Mundial",
    layout="wide"
)

# =============================
# IMPORTS
# =============================
from modules.login import login_page
from modules.partidos import partidos_page
from modules.predicciones import predicciones_page
from modules.resultados import resultados_page
from modules.ranking import ranking_page
from modules.historial import historial_page
from modules.movimientos import movimientos_page
from modules.home import home_page
from modules.resultados_partido import resultados_partido_page
from utils.data_loader import cargar_todo
from modules.finanzas import finanzas_page
from modules.admin_usuarios import admin_usuarios_page

if "usuario" not in st.session_state:

    login_page()
    st.stop()

# =============================
# PRECARGA DE DATOS
# se ejecuta solo si el cache expiró
# =============================

if "data_loaded" not in st.session_state:

    with st.spinner("Inicializando aplicación..."):

        cargar_todo()

    st.session_state["data_loaded"] = True


USUARIO_ACTUAL = st.session_state.get("usuario")
ROL_ACTUAL = st.session_state.get("rol")

# valores:
# admin
# usuario


# =============================
# MENÚ LATERAL
# =============================

st.sidebar.title("Polla Mundial")


menu_opciones = [

    "Inicio",
    
    "Mis predicciones",

    "Mi historial",

    "Tabla posiciones",

    "Premios por partido"

]


# opciones exclusivas admin

if ROL_ACTUAL == "admin":

    menu_opciones.extend([

        "Resultados",   

        "Movimientos",

        "Finanzas", 

        "Usuarios"

    ])


menu = st.sidebar.radio(

    "Seleccione opción",

    menu_opciones

)


# =============================
# NAVEGACIÓN
# =============================

if menu == "Inicio":
    home_page()

elif menu == "Mis predicciones":

    predicciones_page()


elif menu == "Mi historial":

    historial_page()


elif menu == "Tabla posiciones":

    ranking_page()


elif menu == "Resultados":

    resultados_page()


elif menu == "Movimientos":

    movimientos_page()

elif menu == "Premios por partido":
    resultados_partido_page()

elif menu == "Finanzas":
    finanzas_page()

elif menu == "Usuarios":
    admin_usuarios_page()


# =============================
# INFO USUARIO
# =============================

st.sidebar.divider()

st.sidebar.caption(f"Usuario: {USUARIO_ACTUAL}")

st.sidebar.caption(f"Rol: {ROL_ACTUAL}")

if st.sidebar.button("Cerrar sesión"):
    st.session_state.clear()
    st.rerun()