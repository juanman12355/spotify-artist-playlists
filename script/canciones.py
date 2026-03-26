import requests
import time
from utils import normalizar, es_remastered

BASE_URL = "https://api.spotify.com/v1"

def obtener_track_de_album(token: str, album_id: str) -> list:
    tracks = []
    offset = 0
    while True:
        respuesta = requests.get(f"{BASE_URL}/albums/{album_id}/tracks",
            headers={"Authorization": f"Bearer {token}"},
            params={"limit": 50, "offset": offset, "market": "CO"}
        )
        respuesta.raise_for_status()
        data = respuesta.json()
        items = data.get("items", [])
        if not items:
            break
        tracks.extend(items)
        offset += len(items)
        if not data.get("next"):
            break
    return tracks

def recopilar_tracks(token: str, albumes: list) -> list:
    todas = []
    for i, album in enumerate(albumes, 1):
        print(f"[{i}/{len(albumes)}] {album['name']}")
        tracks = obtener_track_de_album(token, album["id"])
        todas.extend(tracks)
        time.sleep(0.3)
    return todas

def deduplicar(tracks: list) -> list:
    vistos: dict[str, dict] = {}
    for track in tracks:
        clave = normalizar(track["name"])
        if clave not in vistos:
            vistos[clave] = track
        elif es_remastered(track["name"]) and not es_remastered(vistos[clave]["name"]):
            vistos[clave] = track
    return list(vistos.values())