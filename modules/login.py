import streamlit as st
from utils.data_loader import cargar_todo
from utils.dataframe_utils import normalizar_columnas
from utils.security import verificar_password


def login_page():

    st.title("Iniciar sesión")

    usuario = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):

        # 🔥 validar input vacío
        if usuario.strip() == "" or password.strip() == "":
            st.warning("Ingresa usuario y contraseña")
            return

        data = cargar_todo()
        df_users = data["usuarios"]

        df_users = normalizar_columnas(df_users)

        if len(df_users) == 0:
            st.error("No hay usuarios registrados")
            return

        if "usuario_id" not in df_users.columns:
            st.error(f"Columnas detectadas: {list(df_users.columns)}")
            return

        # 🔥 limpiar datos SIEMPRE
        df_users["usuario_id"] = df_users["usuario_id"].astype(str).str.strip()
        df_users["password"] = df_users["password"].astype(str).str.strip()
        df_users["activo"] = df_users["activo"].astype(int)

        usuario_input = str(usuario).strip()
        password_input = str(password).strip()

        user = df_users[
            (df_users["usuario_id"] == usuario_input)
            &
            (df_users["activo"] == 1)
        ]

        if len(user) == 0:
            st.error("Credenciales incorrectas")
            return

        hashed = str(user.iloc[0]["password"]).strip()

        # 🔐 compatibilidad: hash o texto plano
        if hashed.startswith("$2b$"):
            if not verificar_password(password_input, hashed):
                st.error("Credenciales incorrectas")
                return
        else:
            if password_input != hashed:
                st.error("Credenciales incorrectas")
                return

        st.session_state["usuario"] = user.iloc[0]["usuario_id"]
        st.session_state["rol"] = user.iloc[0]["rol"]

        st.success("Bienvenido")
        st.rerun()