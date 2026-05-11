import unicodedata


def limpiar_texto(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto.lower())
        if unicodedata.category(c) != 'Mn'
    ).strip()


def bandera(pais):

    mapa = {
        # América
        "argentina": "ar",
        "brasil": "br",
        "uruguay": "uy",
        "paraguay": "py",
        "chile": "cl",
        "peru": "pe",
        "colombia": "co",
        "ecuador": "ec",
        "venezuela": "ve",
        "bolivia": "bo",
        "mexico": "mx",
        "canada": "ca",
        "estados unidos": "us",
        "usa": "us",
        "costa rica": "cr",
        "panama": "pa",
        "jamaica": "jm",
        "haiti": "ht",

        # Europa
        "espana": "es",
        "francia": "fr",
        "alemania": "de",
        "italia": "it",
        "portugal": "pt",
        # Escocia e Inglaterra tienen códigos distintos en flagcdn
        "inglaterra": "gb-eng",
        "escocia": "gb-sct",
        "gales": "gb-wls",
        "irlanda del norte": "gb-nir",
        "paises bajos": "nl",
        "holanda": "nl",
        "belgica": "be",
        "suiza": "ch",
        "croacia": "hr",
        "serbia": "rs",
        "bosnia": "ba",
        "republica checa": "cz",
        "polonia": "pl",
        "dinamarca": "dk",
        "suecia": "se",
        "noruega": "no",
        "austria": "at",
        "uzbekistan": "uz",

        # África
        "marruecos": "ma",
        "senegal": "sn",
        "egipto": "eg",
        "nigeria": "ng",
        "ghana": "gh",
        "camerun": "cm",
        "costa de marfil": "ci",
        "argelia": "dz",
        "tunisia": "tn",
        "tunez": "tn",
        "sudafrica": "za",
        "cabo verde": "cv",
        "rd congo": "cd",

        # Asia / Oceanía
        "japon": "jp",
        "corea del sur": "kr",
        "arabia saudita": "sa",
        "qatar": "qa",
        "iran": "ir",
        "irak": "iq",
        "jordania": "jo",
        "turquia": "tr",
        "australia": "au",
        "nueva zelanda": "nz",
        "nueva zelandia": "nz",
        "curazao": "cw",
    }

    pais_limpio = limpiar_texto(pais)

    codigo = mapa.get(pais_limpio)

    if not codigo:
        return "https://via.placeholder.com/40x30?text=?"

    return f"https://flagcdn.com/w40/{codigo}.png"
