from utils.data_loader import cargar_todo


def saldo_usuario(usuario_id):

    data = cargar_todo()

    df_mov = data["movimientos"]

    if len(df_mov) == 0:
        return 0

    # normalizar a minúsculas para que coincida con la normalización del data_loader
    usuario_id_lower = str(usuario_id).strip().lower()

    df_user = df_mov[df_mov["usuario_id"] == usuario_id_lower]

    if len(df_user) == 0:
        return 0

    return float(df_user["monto"].sum())
