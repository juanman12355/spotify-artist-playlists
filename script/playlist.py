import requests

BASE_URL = "https://api.spotify.com/v1"

# Crea una playlist privada y devuelve su info.
# def crear_playlist(token: str, user_id: str, nombre: str, descripcion: str = "") -> dict:
#     respuesta = requests.post(f"{BASE_URL}/users/{user_id}/playlists",
#         headers={"Authorization": f"Bearer {token}",
#                  "Content-Type": "application/json"},
#         json={"name": nombre, "public": False,
#               "description": descripcion}
#     )
#     respuesta.raise_for_status()
#     return respuesta.json()

def crear_playlist(token: str, user_id: str, nombre: str, descripcion: str = "") -> dict:
    # Usar /me/playlists en lugar de /users/{id}/playlists
    respuesta = requests.post(
        f"{BASE_URL}/me/playlists",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "name": nombre,
            "public": False,
            "description": descripcion
        }
    )

    if not respuesta.ok:
        print("DEBUG crear_playlist error:", respuesta.status_code, respuesta.json())

    respuesta.raise_for_status()
    return respuesta.json()

# Agrega tracks en lotes de 100 (límite de la API).
def agregar_tracks(token: str, playlist_id: str, uris: list):
    for i in range(0, len(uris), 100):
        lote = uris[i:i + 100]
        respuesta = requests.post(
            f"{BASE_URL}/playlists/{playlist_id}/items",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={"uris": lote}
        )
        if not respuesta.ok:
            print("DEBUG error:", respuesta.json())
        respuesta.raise_for_status()
        print(f"Lote {i // 100 + 1}: {len(lote)} canciones agregadas")

def obtener_usuario_id(token: str) -> str:
    respuesta = requests.get(f"{BASE_URL}/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    respuesta.raise_for_status()
    return respuesta.json()["id"]