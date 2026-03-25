import os
import json
import time
import base64
import secrets
import webbrowser
import requests
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urlencode, urlparse, parse_qs

# Load .env from /config/.env
ENV_PATH = Path(__file__).parent.parent / "config" / ".env"
load_dotenv(ENV_PATH)

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
SCOPES = "playlist-modify-private playlist-modify-public"
TOKEN_FILE = Path(__file__).parent.parent / "config" / ".token_cache.json"

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"

def guardar_token(token_data:dict):
    token_data["expires_at"] = time.time() + token_data["expires_in"]
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)

def cargar_token() -> dict | None:
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE) as f:
            return json.load(f)
    return None

def refrescar_token(refresh_token: str) -> dict:
    credenciales = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    respuesta = requests.post(TOKEN_URL, headers={
        "Authorization": f"Basic {credenciales}",
        "Content-Type": "application/x-www-form-urlencoded"
    }, data={
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    })
    respuesta.raise_for_status()
    nuevo = respuesta.json()

    if "refresh_token" not in nuevo:
        nuevo["refresh_token"] = refresh_token
    guardar_token(nuevo)
    return nuevo

def flujo_autorizacion() -> dict:
    state = secrets.token_urlsafe(16)
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": state
    }  
    url = f"{AUTH_URL}?{urlencode(params)}"
    print("\n Abriendo el navegador para autorizar la app.")
    print (f"Si no se abre, ve manualmente a:\n {url}\n")

    print(f"\n🔐 Abre esta URL en una ventana de incógnito:\n\n   {url}\n")

    # webbrowser.open(url)

    url_respuesta = input("Pega aqui la URL completa a la que fuiste redirigido: \n>").strip()
    parsed = urlparse(url_respuesta)
    code = parse_qs(parsed.query).get("code", [None])[0]
    if not code:
        raise ValueError("No se encontró el código de autorizacion en la URL.")
    
    credenciales = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    
    respuesta = requests.post(TOKEN_URL, headers={
        "Authorization": f"Basic {credenciales}",
        "Content-Type": "application/x-www-form-urlencoded"
    }, data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    })

    respuesta.raise_for_status()
    token_data = respuesta.json()
    guardar_token(token_data)
    print("Autorizacion exitosa.\n")
    return token_data

def obtener_token() -> str:
    token_data = cargar_token()

    if token_data:
        if time.time() < token_data.get("expires_at", 0)-60:
            return token_data["access_token"]
        # Expired token - refresh
        print("Refrescando token.")
        token_data = refrescar_token(token_data["refresh_token"])
        return token_data["access_token"]
    
    # No token saved - complete execution
    token_data = flujo_autorizacion()
    return token_data["access_token"]

def headers(token:str) -> dict:
    return{"Authorization": f"Bearer {token}"}