import sys
from auth import obtener_token
from artista import buscar_artista, obtener_todos_los_albumes, seleccionar_mejor_version
from canciones import recopilar_tracks, deduplicar
from playlist import crear_playlist, agregar_tracks, obtener_usuario_id


def crear_playlist_artista(nombre_artista: str):
    # 1. Autenticación
    print("Verificando autenticación.")
    token = obtener_token()

    # 2. Buscar artista
    print(f"\n Buscando artista: {nombre_artista}.")
    artista = buscar_artista(token, nombre_artista)
    nombre_oficial = artista["name"]
    artist_id = artista["id"]
    print(f"Encontrado: {nombre_oficial} (ID: {artist_id})")

    # 3. Obtener álbumes
    print("\n Obteniendo álbumes.")
    todos = obtener_todos_los_albumes(token, artist_id)
    seleccionados = seleccionar_mejor_version(todos)
    print(f"{len(seleccionados)} álbumes únicos (de {len(todos)} totales)")

    # 4. Recopilar canciones
    print("\n Recopilando canciones.")
    todas_las_tracks = recopilar_tracks(token, seleccionados)

    # 5. Deduplicar
    tracks_unicas = deduplicar(todas_las_tracks)
    print(f"\n {len(tracks_unicas)} canciones únicas (de {len(todas_las_tracks)} totales)")

    # 6. Crear playlist
    print("\n Creando playlist.")
    user_id = obtener_usuario_id(token)
    playlist = crear_playlist(
        token, user_id,
        nombre=nombre_oficial,
        descripcion=f"Discografía completa de {nombre_oficial} - Creada automáticamente"
    )
    print(f"Playlist '{nombre_oficial}' creada (privada)")

    # 7. Agregar canciones
    print("\n Agregando canciones a la playlist.")
    uris = [t["uri"] for t in tracks_unicas if t.get("uri")]
    agregar_tracks(token, playlist["id"], uris)

    print(f"\n Listo! {len(uris)} canciones en la playlist.")
    print(f"{playlist['external_urls']['spotify']}")


if __name__ == "__main__":
    nombre = input("Nombre del artista: ").strip()
    if not nombre:
        print("Debes ingresar un nombre.")
        sys.exit(1)
    crear_playlist_artista(nombre)