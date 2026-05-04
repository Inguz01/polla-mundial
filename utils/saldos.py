from utils.data_loader import cargar_todo


def saldo_usuario(usuario_id):

    data = cargar_todo()

    df_mov = data["movimientos"]

    if len(df_mov) == 0:
        return 0

    df_user = df_mov[df_mov["usuario_id"] == usuario_id]

    if len(df_user) == 0:
        return 0

    return float(df_user["monto"].sum())