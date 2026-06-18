import pandas as pd

from sqlalchemy import text

from database.postgres import engine
from database.postgres import SessionLocal
from database.models import Configuracion
from database.models import Resultado
#from utils.helpers import generar_id

from database.models import Movimiento
from utils.helpers import generar_id
from datetime import datetime
from database.models import Prediccion

from database.models import Usuario
from utils.security import hash_password


def obtener_config():

    session = SessionLocal()

    try:

        registros = session.query(
            Configuracion
        ).all()

        return [
            {
                "clave": r.clave,
                "valor": r.valor
            }
            for r in registros
        ]

    finally:
        session.close()

def obtener_tabla(nombre_tabla):

    query = f"SELECT * FROM {nombre_tabla}"

    return pd.read_sql(
        text(query),
        engine
    )

def guardar_resultado(
    partido_id,
    goles_local,
    goles_visitante
):

    session = SessionLocal()

    try:

        existente = (
            session.query(Resultado)
            .filter(
                Resultado.partido_id == partido_id
            )
            .first()
        )

        if existente:

            existente.goles_local = goles_local
            existente.goles_visitante = goles_visitante

        else:

            nuevo = Resultado(
                id=generar_id(),
                partido_id=partido_id,
                goles_local=goles_local,
                goles_visitante=goles_visitante
            )

            session.add(nuevo)

        session.commit()

    finally:

        session.close()

def guardar_movimientos(lista):

    if not lista:
        return

    session = SessionLocal()

    try:

        for m in lista:

            fecha_liquidacion = m.get(
                "fecha_liquidacion"
            )

            if isinstance(
                fecha_liquidacion,
                str
            ):
                fecha_liquidacion = pd.to_datetime(
                    fecha_liquidacion
                ).to_pydatetime()

            movimiento = Movimiento(
                id=generar_id(),
                usuario_id=str(
                    m["usuario_id"]
                ).strip().lower(),
                fecha=datetime.now(),
                tipo=m["tipo"],
                referencia=m["referencia"],
                monto=m["monto"],
                fecha_liquidacion=fecha_liquidacion
            )

            session.add(movimiento)

        session.commit()

    finally:

        session.close()

def guardar_prediccion(
    usuario_id,
    partido_id,
    goles_local,
    goles_visitante
):

    session = SessionLocal()

    try:

        existente = (
            session.query(Prediccion)
            .filter(
                Prediccion.usuario_id == usuario_id,
                Prediccion.partido_id == partido_id
            )
            .first()
        )

        if existente:

            existente.goles_local = goles_local
            existente.goles_visitante = goles_visitante
            existente.participa = True
            existente.pago_validado = False

        else:

            nueva = Prediccion(
                id=generar_id(),
                usuario_id=usuario_id,
                partido_id=partido_id,
                goles_local=goles_local,
                goles_visitante=goles_visitante,
                participa=True,
                pago_validado=False
            )

            session.add(nueva)

        session.commit()

    finally:

        session.close()

def eliminar_prediccion(
    usuario_id,
    partido_id
):

    session = SessionLocal()

    try:

        filas = (
            session.query(Prediccion)
            .filter(
                Prediccion.usuario_id == usuario_id,
                Prediccion.partido_id == partido_id
            )
            .delete()
        )

        session.commit()

        return filas > 0

    finally:

        session.close()


def crear_usuario(usuario_id, password, rol):

    session = SessionLocal()

    try:

        usuario_id = usuario_id.strip().lower()

        existente = (
            session.query(Usuario)
            .filter(Usuario.usuario_id == usuario_id)
            .first()
        )

        if existente:
            return False, "El usuario ya existe"

        nuevo = Usuario(
            usuario_id=usuario_id,
            password=hash_password(password),
            rol=rol,
            activo=True
        )

        session.add(nuevo)
        session.commit()

        return True, "Usuario creado"

    finally:
        session.close()

def actualizar_estado_usuario(usuario_id, activo):

    session = SessionLocal()

    try:

        usuario = (
            session.query(Usuario)
            .filter(Usuario.usuario_id == usuario_id)
            .first()
        )

        if usuario is None:
            return False

        usuario.activo = bool(activo)

        session.commit()

        return True

    finally:

        session.close()

def actualizar_password(usuario_id, nueva_password):

    session = SessionLocal()

    try:

        usuario = (
            session.query(Usuario)
            .filter(Usuario.usuario_id == usuario_id)
            .first()
        )

        if usuario is None:
            return False

        usuario.password = hash_password(nueva_password)

        session.commit()

        return True

    finally:

        session.close()

