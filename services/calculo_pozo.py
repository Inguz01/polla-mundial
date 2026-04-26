from settings import PORCENTAJE_ADMIN


def calcular_pozo(total_recaudado):

    # validar entrada
    try:
        total = float(total_recaudado)
    except:
        total = 0

    if total < 0:
        total = 0

    # cálculo
    admin = total * PORCENTAJE_ADMIN
    pozo = total - admin

    # redondeo (evita decimales raros)
    admin = round(admin, 2)
    pozo = round(pozo, 2)

    return admin, pozo