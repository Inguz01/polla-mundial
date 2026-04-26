from utils.data_loader import cargar_todo


def obtener_config():

    data = cargar_todo()

    df = data["config"]

    config = {}

    for _, row in df.iterrows():

        config[row["clave"]] = float(row["valor"])

    return config



def valor_apuesta_por_fase(fase):

    config = obtener_config()

    mapa = {

        "grupos": config.get("valor_grupos", 5000),

        "octavos": config.get("valor_octavos", 8000),

        "cuartos": config.get("valor_cuartos", 10000),

        "semifinal": config.get("valor_semifinal", 15000),

        "final": config.get("valor_final", 20000),

    }

    return mapa.get(fase.lower(), 5000)



def porcentaje_admin():

    config = obtener_config()

    return config.get("porcentaje_admin", 0.10)