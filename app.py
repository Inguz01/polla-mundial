import streamlit as st

# =============================
# CONFIGURACIÓN INICIAL
# =============================

st.set_page_config(
    page_title="Polla Mundial",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# =============================
# CSS MOBILE-FIRST
# =============================

st.markdown("""
<style>

/* CONTENEDOR GENERAL */

.block-container {
    padding-top: 1rem;
    padding-bottom: 3rem;
    padding-left: 1rem;
    padding-right: 1rem;
    max-width: 900px;
}

/* BOTONES */

.stButton button {
    width: 100%;
    border-radius: 12px;
    height: 3em;
    font-size: 16px;
    font-weight: 600;
}

/* INPUTS */

.stNumberInput input {
    font-size: 18px;
    text-align: center;
}

/* NUMBER INPUT MÁS COMPACTO */
            
div[data-testid="stNumberInput"] {
    max-width: 90px;
}            

/* SELECTBOX */

.stSelectbox div[data-baseweb="select"] {
    border-radius: 10px;
}

/* SIDEBAR */

section[data-testid="stSidebar"] {
    width: 260px !important;
}

/* MÉTRICAS */

div[data-testid="metric-container"] {
    border-radius: 12px;
    padding: 10px;
}

/* MOBILE */

@media (max-width: 768px) {

    .block-container {
        padding-top: 0.5rem;
        padding-left: 0.7rem;
        padding-right: 0.7rem;
    }

    h1 {
        font-size: 28px !important;
    }

    h2 {
        font-size: 22px !important;
    }

    h3 {
        font-size: 18px !important;
    }

    p, label, span {
        font-size: 15px !important;
    }

    .stButton button {
        height: 3.2em;
        font-size: 16px;
    }
}

</style>
""", unsafe_allow_html=True)

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

# =============================
# LOGIN
# =============================

if "usuario" not in st.session_state:

    login_page()
    st.stop()

# =============================
# PRECARGA DE DATOS
# =============================

if "data_loaded" not in st.session_state:

    with st.spinner("Inicializando aplicación..."):

        cargar_todo()

    st.session_state["data_loaded"] = True

# =============================
# SESIÓN
# =============================

USUARIO_ACTUAL = st.session_state.get("usuario")
ROL_ACTUAL = st.session_state.get("rol")

# =============================
# MENÚ LATERAL
# =============================

st.sidebar.title("⚽ Polla Mundial")

menu_opciones = [

    "Reglas de juego",

    "Mis pronósticos",

    "Mi historial",

    "Tabla de posiciones",

    "Premios por partido"

]

# =============================
# OPCIONES ADMIN
# =============================

if ROL_ACTUAL == "admin":

    menu_opciones = [

        "Reglas de juego",

        "Gestionar usuarios",

        "Registrar marcadores",

        "Liquidar partidos",

        "Tabla de posiciones",

        "Registrar movimientos financieros",

        "Dashboard financiero"

    ]

# =============================
# MENÚ
# =============================

menu = st.sidebar.radio(

    "Seleccione opción",

    menu_opciones

)

# =============================
# NAVEGACIÓN
# =============================

if menu == "Reglas de juego":

    home_page()

elif menu == "Mis pronósticos":

    predicciones_page()

elif menu == "Mi historial":

    historial_page()

elif menu == "Tabla de posiciones":

    ranking_page()

elif menu == "Premios por partido":

    resultados_partido_page()

# =============================
# ADMIN
# =============================

elif menu == "Gestionar usuarios":

    admin_usuarios_page()

elif menu == "Registrar marcadores":

    resultados_page()

elif menu == "Liquidar partidos":

    resultados_partido_page()

elif menu == "Registrar movimientos financieros":

    movimientos_page()

elif menu == "Dashboard financiero":

    finanzas_page()

# =============================
# FOOTER SIDEBAR
# =============================

st.sidebar.divider()

st.sidebar.caption(f"👤 Usuario: {USUARIO_ACTUAL}")

st.sidebar.caption(f"🔐 Rol: {ROL_ACTUAL}")

if st.sidebar.button("Cerrar sesión"):

    st.session_state.clear()

    st.rerun()