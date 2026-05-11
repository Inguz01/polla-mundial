import streamlit as st

from utils.data_loader import cargar_todo
from utils.security import verificar_password


def login_page():

    # =========================
    # HERO LOGIN
    # =========================

    st.markdown("""
    <div style='padding:50px 30px;
    border-radius:28px;
    background:linear-gradient(135deg, rgba(37,99,235,0.20), rgba(220,38,38,0.16), rgba(22,163,74,0.14)), rgba(16,24,39,0.92);
    border:1px solid rgba(255,255,255,0.08);
    backdrop-filter:blur(12px);
    text-align:center;
    margin-top:40px;
    margin-bottom:30px;'>

    <div style='font-size:80px;margin-bottom:10px;'>
    🏆
    </div>

    <div style='font-size:64px;font-weight:700;color:white;line-height:1;'>
    POLLA MUNDIAL
    </div>

    <div style='font-size:40px;font-weight:700;color:#FACC15;margin-top:8px;'>
    SOMOS 26
    </div>

    <div style='margin-top:20px;font-size:18px;color:#D1D5DB;'>
    Predice. Compite. Gana.
    </div>

    </div>
    """, unsafe_allow_html=True)

    # =========================
    # FORM LOGIN
    # =========================

    st.markdown("### 🔐 Iniciar sesión")

    usuario = st.text_input(
        "Usuario"
    )

    password = st.text_input(
        "Contraseña",
        type="password"
    )

    # =========================
    # LOGIN
    # =========================

    if st.button(
        "Ingresar",
        use_container_width=True
    ):

        # =========================
        # VALIDACIÓN INPUT
        # =========================

        if usuario.strip() == "" or password.strip() == "":
            st.warning("Ingresa usuario y contraseña")
            return

        # =========================
        # CARGA DATOS
        # =========================

        data = cargar_todo()

        df_users = data.get("usuarios")

        if df_users is None or len(df_users) == 0:
            st.error("No hay usuarios registrados")
            return

        # =========================
        # LIMPIEZA COLUMNAS
        # =========================

        df_users.columns = [
            str(c).strip().lower()
            for c in df_users.columns
        ]

        # =========================
        # VALIDAR COLUMNAS
        # =========================

        columnas_requeridas = [

            "usuario_id",
            "password",
            "rol",
            "activo"

        ]

        for col in columnas_requeridas:

            if col not in df_users.columns:

                st.error(f"Falta columna: {col}")

                return

        # =========================
        # LIMPIEZA DATA
        # =========================

        df_users["usuario_id"] = (

            df_users["usuario_id"]

            .astype(str)

            .str.strip()

            .str.lower()

        )

        df_users["password"] = (
            df_users["password"]
            .astype(str)
        )

        df_users["rol"] = (

            df_users["rol"]

            .astype(str)

            .str.strip()

        )

        df_users["activo"] = (

            df_users["activo"]

            .fillna(0)

            .astype(int)

        )

        usuario_input = (
            str(usuario)
            .strip()
            .lower()
        )

        password_input = str(password)

        # =========================
        # VALIDAR USUARIO
        # =========================

        user_all = df_users[
            df_users["usuario_id"] == usuario_input
        ]

        if len(user_all) == 0:

            st.error("Credenciales incorrectas")

            return

        # =========================
        # VALIDAR ACTIVO
        # =========================

        if int(user_all.iloc[0]["activo"]) == 0:

            st.warning("Usuario inactivo")

            return

        # =========================
        # VALIDAR PASSWORD
        # =========================

        hashed = str(
            user_all.iloc[0]["password"]
        ).strip()

        # Sheets puede devolver contraseñas numéricas como float ("1234.0")
        # se normaliza a entero string para que coincida con lo que escribe el usuario
        if not hashed.startswith("$2b$"):
            try:
                hashed = str(int(float(hashed)))
            except (ValueError, TypeError):
                pass

        if hashed.startswith("$2b$"):

            if not verificar_password(
                password_input,
                hashed
            ):

                st.error("Credenciales incorrectas")

                return

        else:

            if password_input != hashed:

                st.error("Credenciales incorrectas")

                return

        # =========================
        # LOGIN OK
        # =========================

        st.session_state["usuario"] = (
            user_all.iloc[0]["usuario_id"]
        )

        st.session_state["rol"] = (
            user_all.iloc[0]["rol"]
        )

        st.session_state["login_ok"] = True

        st.rerun()