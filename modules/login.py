import streamlit as st
from utils.data_loader import cargar_todo
from utils.dataframe_utils import normalizar_columnas


def login_page():

    st.title("Iniciar sesión")

    usuario = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):

        data = cargar_todo()
        df_users = data["usuarios"]

        # 🔥 normalizar columnas SIEMPRE
        df_users = normalizar_columnas(df_users)

        # 🔥 VALIDACIÓN CORRECTA
        if "usuario_id" not in df_users.columns:
            st.error(f"Columnas detectadas: {list(df_users.columns)}")
            st.stop()

        # 🔥 limpiar tipos y espacios
        df_users["usuario_id"] = df_users["usuario_id"].astype(str).str.strip()
        df_users["password"] = df_users["password"].astype(str).str.strip()
        df_users["activo"] = df_users["activo"].astype(int)

        usuario_input = str(usuario).strip()
        password_input = str(password).strip()

        user = df_users[
            (df_users["usuario_id"] == usuario_input)
            &
            (df_users["password"] == password_input)
            &
            (df_users["activo"] == 1)
        ]

        if len(user) == 0:
            st.error("Credenciales incorrectas")
            return

        st.session_state["usuario"] = user.iloc[0]["usuario_id"]
        st.session_state["rol"] = user.iloc[0]["rol"]

        st.success("Bienvenido")
        st.rerun()