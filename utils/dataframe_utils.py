import pandas as pd


def normalizar_columnas(df):

    if df is None or len(df) == 0:
        return df

    # 🔥 solo normalizar nombres de columnas
    df.columns = [str(c).strip().lower() for c in df.columns]

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