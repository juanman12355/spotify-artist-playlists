import re
from unicodedata import normalize as unorm

KEYWORDS_EN_VIVO = [
    "live", "en vivo", "en directo", "concert", "concierto",
    "unplugged", "mtv", "tour", "at the", "wembley", "glastonbury",
    "recorded at", "acoustic live"
]

KEYWORDS_REMASTERED = [
    "remaster", "remastered", "remasterizado", "deluxe",
    "anniversary", "aniversario", "expanded", "special edition"
]

def normalizar(texto: str) -> str:
    texto = texto.lower().strip
    texto = unorm("NFD", texto).encode("ascii", "ignore").decode("utf-8")
    texto = re.sub(r"[^a-z0-9\s]", "", texto)
    return re.sub(r"\s+", " ", texto).strip()

def es_en_vivo(nombre: str) -> bool:
    n = normalizar(nombre)
    return any(kw in n for kw in KEYWORDS_EN_VIVO)

def es_remastered(nombre:str) -> bool:
    n = normalizar(nombre)
    return any(kw in n for kw in KEYWORDS_REMASTERED)

def nombre_base_album(nombre:str) -> str:
    limpio = re.sub(
        r"[\(\[].{0,40}(remaster|deluxe|anniversary|edition|expanded|special).{0,20}[\)\]]",
        "", nombre, flags=re.IGNORECASE
    )
    return normalizar(limpio)