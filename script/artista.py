import requests
from utils import es_en_vivo, es_remastered, nombre_base_album

BASE_URL = "https://api.spotify.com/v1"

def buscar_artista(token: str, nombre:str) -> dict:
    respuesta = requests.get(f"{BASE_URL}/search", headers={
        "Authorization": f"Bearer {token}"
    }, params={"q": f"artist:{nombre}", "type": "artist", "limit": 1})
    respuesta.raise_for_status()
    artistas = respuesta.json()["artists"]["items"]
    if not artistas:
        raise ValueError(f"Artista '{nombre}' no encontrado.")
    return artistas[0]

def obtener_albumes_paginados(token: str, artist_id: str, tipo: str) -> list:
    albumes = []
    offset = 0
    while True:
        respuesta = requests.get(
            f"{BASE_URL}/artists/{artist_id}/albums",
            headers={"Authorization":f"Bearer {token}"},
            params={"include_groups": tipo, "limit": 10,
                    "offset": offset, "market": "CO"}
        )
        respuesta.raise_for_status()
        data = respuesta.json()
        items = data.get("items", [])
        if not items:
            break
        for album in items:
            if not es_en_vivo(album["name"]):
                albumes.append(album)
        offset += len(items)
        if not data.get("next"):
            break
    return albumes

def obtener_todos_los_albumes(token: str, artist_id: str) -> list:
    albumes = []
    for tipo in ["album", "single"]:
        albumes.extend(obtener_albumes_paginados(token, artist_id, tipo))
    return albumes

def seleccionar_mejor_version(albumes: list) -> list:
    grupos: dict[str, list] = {}
    for album in albumes:
        base = nombre_base_album(album["name"])
        grupos.setdefault(base, []).append(album)

    seleccionados = []
    for grupo in grupos.values():
        remastered = [a for a in grupo if es_remastered(a["name"])]
        seleccionados.append(remastered[0] if remastered else grupo[0])
    return seleccionados