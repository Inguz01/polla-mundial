print("INICIANDO")

from database.google_sheets import connect

print("IMPORT OK")

from database.postgres import engine

import pandas as pd


db = connect()

print("CONEXION OK")

def migrar_hoja(nombre_hoja, nombre_tabla):

    print(f"Migrando {nombre_hoja}...")

    sheet = db.worksheet(nombre_hoja)

    registros = sheet.get_all_records()

    df = pd.DataFrame(registros)

    print("COLUMNAS ORIGINALES:")
    print(repr(df.columns.tolist()))

    # Eliminar columnas sin nombre
    df = df[[c for c in df.columns if str(c).strip()]]

    # Ajustes de tipos

    if nombre_tabla == "usuarios":

        df["activo"] = (
            df["activo"]
            .astype(int)    
            .astype(bool)
        )

    if nombre_tabla == "predicciones":

        df["participa"] = (
            df["participa"]
            .astype(int)
            .astype(bool)
        )

        df["pago_validado"] = (
            df["pago_validado"]
            .astype(int)
            .astype(bool)
        )

    if nombre_tabla == "partidos":

        df = df.drop(
            columns=["valor"],
            errors="ignore"
        )    

    print(f"Registros: {len(df)}")
    print(df.columns.tolist())
    print(df.dtypes)

    df.to_sql(
        nombre_tabla,
        engine,
        if_exists="append",
        index=False
    )

    print(f"OK -> {nombre_tabla}")

#migrar_hoja("usuarios", "usuarios")

#migrar_hoja("partidos", "partidos")

#migrar_hoja("equipos", "equipos")

#migrar_hoja("predicciones", "predicciones")

#migrar_hoja("resultados", "resultados")

migrar_hoja("movimientos", "movimientos")

migrar_hoja("config", "configuracion")