# crear_playlist_artista.py
import os
import re
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pathlib import Path
from dotenv import load_dotenv
from unicodedata import normalize

# Load .env from /config/.env
ENV_PATH = Path(__file__).parent.parent / "config" / ".env"
load_dotenv(ENV_PATH)

load_dotenv()

SCOPE = "playlist-modify-private playlist-modify-public ugc-image-upload"

def normalizar(texto: str) -> str:
    """Normaliza texto para comparación: minúsculas, sin acentos, sin signos."""
    texto = texto.lower().strip()
    texto = normalize("NFD", texto).encode("ascii", "ignore").decode("utf-8")
    texto = re.sub(r"[^a-z0-9\s]", "", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto

def es_en_vivo(nombre: str) -> bool:
    """Detecta si un álbum es grabación en vivo."""
    keywords = ["live", "en vivo", "en directo", "concert", "concierto",
                "acoustic", "unplugged", "mtv", "tour", "at the", "at madison",
                "wembley", "glastonbury", "recorded at"]
    nombre_norm = normalizar(nombre)
    return any(kw in nombre_norm for kw in keywords)

def es_remastered(nombre: str) -> bool:
    """Detecta si un álbum tiene sufijo de remasterización."""
    keywords = ["remaster", "remastered", "remasterizado", "deluxe",
                "anniversary", "aniversario", "expanded", "special edition"]
    nombre_norm = normalizar(nombre)
    return any(kw in nombre_norm for kw in keywords)

def nombre_base_album(nombre: str) -> str:
    """Extrae el nombre base de un álbum quitando sufijos de edición."""
    # Elimina paréntesis/corchetes con contenido tipo "(Remastered)", "[Deluxe Edition]", etc.
    limpio = re.sub(r"[\(\[].{0,40}(remaster|deluxe|anniversary|edition|expanded|special).{0,20}[\)\]]",
                    "", nombre, flags=re.IGNORECASE)
    return normalizar(limpio)

def obtener_todos_los_albumes(sp: spotipy.Spotify, artist_id: str) -> list:
    """Obtiene álbumes y singles del artista, filtrando lives."""
    albumes = []
    token = sp.auth_manager.get_access_token(as_dict=False)
    headers = {"Authorization": f"Bearer {token}"}

    for tipo in ["album", "single"]:
        offset=0
        while True:
            url = "https://api.spotify.com/v1/artists/{}/albums".format(artist_id)
            params = {
                "include_groups": tipo,
                "limit": 10,
                "offset": offset,
                "market": "CO"
            }
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

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

def seleccionar_mejor_album_por_nombre(albumes: list) -> list:
    """
    Agrupa álbumes por nombre base y se queda con la versión
    remasterizada/deluxe si existe; de lo contrario, con la primera disponible.
    """
    grupos: dict[str, list] = {}
    for album in albumes:
        base = nombre_base_album(album["name"])
        grupos.setdefault(base, []).append(album)

    seleccionados = []
    for base, grupo in grupos.items():
        remastered = [a for a in grupo if es_remastered(a["name"])]
        seleccionados.append(remastered[0] if remastered else grupo[0])
    return seleccionados

def obtener_tracks_de_album(sp: spotipy.Spotify, album_id: str) -> list:
    """Obtiene todas las pistas de un álbum."""
    tracks = []
    resultado = sp.album_tracks(
        album_id, 
        limit=50
    )
    while resultado:
        tracks.extend(resultado["items"])
        resultado = sp.next(resultado) if resultado["next"] else None
    return tracks

def deduplicar_canciones(tracks: list) -> list:
    """
    Elimina duplicados por nombre normalizado.
    Prioriza canciones que tengan 'remaster' en el nombre.
    """
    vistos: dict[str, dict] = {}
    for track in tracks:
        nombre_norm = normalizar(track["name"])
        if nombre_norm not in vistos:
            vistos[nombre_norm] = track
        else:
            # Si la nueva es remastered y la existente no, reemplaza
            if es_remastered(track["name"]) and not es_remastered(vistos[nombre_norm]["name"]):
                vistos[nombre_norm] = track
    return list(vistos.values())

def agregar_tracks_en_lotes(sp: spotipy.Spotify, playlist_id: str, uris: list):
    """Agrega tracks a la playlist en lotes de 100 (límite de la API)."""
    for i in range(0, len(uris), 100):
        sp.playlist_add_items(playlist_id, uris[i:i+100])

def crear_playlist_artista(nombre_artista: str):
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback"),
        scope=SCOPE
    ))

    # 1. Buscar artista
    print(f"🔍 Buscando artista: {nombre_artista}...")
    resultado = sp.search(q=f"artist:{nombre_artista}", type="artist", limit=1)
    artistas = resultado["artists"]["items"]
    if not artistas:
        print("❌ Artista no encontrado.")
        return

    artista = artistas[0]
    artist_id = artista["id"]
    nombre_oficial = artista["name"]
    print(f"✅ Artista encontrado: {nombre_oficial} (ID: {artist_id})")

    # 2. Obtener álbumes (sin lives)
    print("📀 Obteniendo álbumes...")
    todos_albumes = obtener_todos_los_albumes(sp, artist_id)
    albumes_seleccionados = seleccionar_mejor_album_por_nombre(todos_albumes)
    print(f"   {len(albumes_seleccionados)} álbumes únicos seleccionados (de {len(todos_albumes)} totales)")

    # 3. Obtener todas las canciones
    print("🎵 Recopilando canciones...")
    todas_las_tracks = []
    for album in albumes_seleccionados:
        tracks = obtener_tracks_de_album(sp, album["id"])
        todas_las_tracks.extend(tracks)

    # 4. Deduplicar
    tracks_unicas = deduplicar_canciones(todas_las_tracks)
    print(f"   {len(tracks_unicas)} canciones únicas (de {len(todas_las_tracks)} totales)")

    # 5. Crear playlist privada
    usuario = sp.me()["id"]
    playlist = sp.user_playlist_create(
        user=usuario,
        name=nombre_oficial,
        public=False,
        description=f"Discografía completa de {nombre_oficial} · Creada automáticamente"
    )
    playlist_id = playlist["id"]
    print(f"📋 Playlist '{nombre_oficial}' creada (privada)")

    # 6. Agregar canciones
    uris = [t["uri"] for t in tracks_unicas if t.get("uri")]
    agregar_tracks_en_lotes(sp, playlist_id, uris)
    print(f"✅ {len(uris)} canciones agregadas a la playlist.")
    print(f"🔗 URL: {playlist['external_urls']['spotify']}")

if __name__ == "__main__":
    artista = input("Nombre del artista: ").strip()
    crear_playlist_artista(artista)