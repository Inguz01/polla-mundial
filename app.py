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

/* =========================
FUENTES
========================= */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Bebas+Neue&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* =========================
FONDO GENERAL
========================= */

.stApp {
    background:
        radial-gradient(circle at top left, rgba(37,99,235,0.15), transparent 25%),
        radial-gradient(circle at top right, rgba(220,38,38,0.12), transparent 25%),
        radial-gradient(circle at bottom, rgba(22,163,74,0.10), transparent 25%),
        #050816;
    
    color: #F3F4F6;
}

/* =========================
CONTENEDOR
========================= */

.block-container {

    padding-top: 1rem;
    padding-bottom: 3rem;

    padding-left: 2rem;
    padding-right: 2rem;
}

/* =========================
TÍTULOS
========================= */

h1, h2, h3 {
    font-family: 'Bebas Neue', sans-serif !important;
    letter-spacing: 1px;
    color: white;
}

h1 {
    font-size: 54px !important;
}

/* =========================
SIDEBAR
========================= */

section[data-testid="stSidebar"] {

    background: linear-gradient(
        180deg,
        #0B1220 0%,
        #111827 100%
    );

    border-right: 1px solid rgba(255,255,255,0.06);
}

/* =========================
SIDEBAR TEXTOS
========================= */

section[data-testid="stSidebar"] * {
    color: #F3F4F6 !important;
}

/* =========================
RADIO BUTTONS
========================= */

div[role="radiogroup"] label {

    background: transparent;
    border-radius: 12px;
    padding: 8px 12px;
    margin-bottom: 6px;
    transition: all 0.2s ease;
}

div[role="radiogroup"] label:hover {

    background: rgba(37,99,235,0.12);
}

/* =========================
BOTONES
========================= */

.stButton button {

    width: 100%;

    border-radius: 14px;

    border: none;

    background: linear-gradient(
        90deg,
        #2563EB,
        #16A34A
    );

    color: white;

    font-weight: 700;

    height: 3.1em;

    font-size: 16px;

    transition: all 0.25s ease;
}

/* =========================
BOTONES HOVER
========================= */

.stButton button:hover {

    transform: scale(1.02);

    box-shadow:
        0 0 16px rgba(37,99,235,0.35);
}

/* =========================
INPUTS
========================= */

.stTextInput input,
.stNumberInput input,
.stSelectbox div[data-baseweb="select"] {

    border-radius: 12px !important;

    background: #111827 !important;

    color: white !important;

    border: 1px solid rgba(255,255,255,0.08) !important;
}

            
/* INPUTS OSCUROS */

.stTextInput input,
.stNumberInput input,
.stSelectbox div[data-baseweb="select"] {

    background-color: #111827 !important;

    color: white !important;

    border-radius: 12px !important;

    border: 1px solid rgba(255,255,255,0.08) !important;
}

/* =========================
NUMBER INPUTS
========================= */

div[data-testid="stNumberInput"] {
    width: 90px;
}

div[data-testid="stNumberInput"] input {

    text-align: center !important;

    font-size: 18px !important;

    font-weight: 700 !important;
}

/* =========================
DATAFRAMES
========================= */

[data-testid="stDataFrame"] {

    border-radius: 16px;

    overflow: hidden;

    border: 1px solid rgba(255,255,255,0.06);
}

/* =========================
MÉTRICAS
========================= */

div[data-testid="metric-container"] {

    background: rgba(16,24,39,0.9);

    border-radius: 18px;

    padding: 18px;

    border: 1px solid rgba(255,255,255,0.06);
}

/* =========================
EXPANDERS
========================= */

.streamlit-expanderHeader {

    font-size: 18px !important;

    font-weight: 700 !important;
}

/* =========================
BADGES / ALERTAS
========================= */

.stAlert {

    border-radius: 14px;
}

/* =========================
MOBILE
========================= */

@media (max-width: 768px) {

    .block-container {

        padding-top: 0.5rem;
        padding-left: 0.7rem;
        padding-right: 0.7rem;
    }

    h1 {
        font-size: 38px !important;
    }

    h2 {
        font-size: 28px !important;
    }

    h3 {
        font-size: 22px !important;
    }

    p, label, span {

        font-size: 15px !important;
    }

    .stButton button {

        height: 3.2em;
    }
            
    .hero-titulo {
        font-size: 38px !important;
    }

    .hero-subtitulo {
        font-size: 24px !important;
    }

    .hero-copa {
        font-size: 48px !important;
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

if st.session_state.get("login_ok"):

    st.session_state.pop("login_ok")

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