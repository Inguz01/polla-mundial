import pandas as pd


def normalizar_columnas(df):

    # convertir nombres a string por seguridad
    df.columns = df.columns.map(str)

    df.columns = (

        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")

    )

    mapa = {

        "golesvisitante": "goles_visitante",
        "goles_visitantes": "goles_visitante",
        "visitante_goles": "goles_visitante",

        "goleslocal": "goles_local",
        "local_goles": "goles_local",

        "usuario": "usuario_id",
        "user": "usuario_id",

        "partido": "partido_id",

        "key": "clave",
        "value": "valor"

    }

    df.rename(columns=mapa, inplace=True)

    return df



def safe_int(value):

    try:

        return int(float(value))

    except:

        return 0



def asegurar_columnas(df, columnas):

    for col in columnas:

        if col not in df.columns:

            df[col] = 0

    return df