from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Date,
    Time,
    DateTime,
    Numeric
)

from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(String(50), unique=True)
    password = Column(String)
    rol = Column(String(20))
    activo = Column(Boolean)


class Partido(Base):
    __tablename__ = "partidos"

    id = Column(Integer, primary_key=True)

    equipo_local = Column(String(100))
    equipo_visitante = Column(String(100))

    fecha = Column(Date)
    hora = Column(Time)

    fase = Column(String(50))
    grupo = Column(String(10))

    estado = Column(String(20))


class Equipo(Base):
    __tablename__ = "equipos"

    equipo = Column(String(100), primary_key=True)

    codigo = Column(String(100))


class Prediccion(Base):
    __tablename__ = "predicciones"

    id = Column(String, primary_key=True)

    usuario_id = Column(String(50))

    partido_id = Column(Integer)

    goles_local = Column(Integer)

    goles_visitante = Column(Integer)

    participa = Column(Boolean)

    pago_validado = Column(Boolean)


class Resultado(Base):
    __tablename__ = "resultados"

    id = Column(String, primary_key=True)

    partido_id = Column(Integer)

    goles_local = Column(Integer)

    goles_visitante = Column(Integer)


class Movimiento(Base):
    __tablename__ = "movimientos"

    id = Column(String, primary_key=True)

    usuario_id = Column(String(50))

    fecha = Column(DateTime)

    tipo = Column(String(50))

    referencia = Column(String(100))

    monto = Column(Numeric)


class Configuracion(Base):
    __tablename__ = "configuracion"

    clave = Column(String(100), primary_key=True)

    valor = Column(String(100))