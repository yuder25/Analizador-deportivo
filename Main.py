import os
import requests
import pytz
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

API_KEY = os.getenv("API_FOOTBALL_KEY", "TU_API_KEY_AQUI")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

COLOMBIA = pytz.timezone("America/Bogota")

def get_fecha_colombia(dias=0):
    return (datetime.now(COLOMBIA).date() + timedelta(days=dias)).isoformat()

def traer_partidos(fecha):
    url = f"{BASE_URL}/fixtures?date={fecha}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        return r.json().get("response", [])
    except:
        return []

def get_ultimos_5(team_id):
    url = f"{BASE_URL}/fixtures?team={team_id}&last=5"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        return r.json().get("response", [])
    except:
        return []

def analizar_racha(team_id, team_name):
    partidos = get_ultimos_5(team_id)
    if len(partidos) < 3:
        return None
    total_goles = 0
    btts = 0
    validos = 0
    for p in partidos:
        g_home = p["goals"]["home"]
        g_away = p["goals"]["away"]
        if g_home is None or g_away is None:
            continue
        validos += 1
        total_goles += g_home + g_away
        if g_home > 0 and g_away > 0:
            btts += 1
    if validos == 0:
        return None
    if btts >= 4:
        return f"🚨 ALERTA BTTS - {team_name}: {btts}/{validos} últimos con ambos marcan"
    if total_goles / validos >= 3.0:
        return f"🚨 ALERTA GOLES - {team_name}: Promedio {total_goles/validos:.1f} goles por partido"
    return None

@app.get("/health")
def health():
    return {"status": "ok", "fecha_colombia": get_fecha_colombia()}

@app.get("/partidos-hoy")
def partidos_hoy():
    hoy = get_fecha_colombia(0)
    manana = get_fecha_colombia(1)
    fixtures = traer_partidos(hoy) + traer_partidos(manana)
    return fixtures[:100]

@app.get("/analizador-completo", response_class=HTMLResponse)
def analizador_completo():
    hoy = get_fecha_colombia(0)
    manana = get_fecha_colombia(1)
    fixtures = traer_partidos(hoy) + traer_partidos(manana)
    fixtures = fixtures[:100]

    alertas = []
    lista_partidos = ""
    for f in fixtures:
        home = f["teams"]["home"]
        away = f["teams"]["away"]
        fecha_hora = f["fixture"]["date"]
        liga = f["league"]["name"]
        lista_partidos += f"<p>⚽ {liga} - {home['name']} vs {away['name']} - {fecha_hora}</p>"
        for team in [home, away]:
            alerta = analizar_racha(team["id"], team["name"])
            if alerta and alerta not in alertas:
                alertas.append(alerta)

    alertas_html = "<br>".join(alertas) if alertas else "Sin alertas de racha 5/5 hoy. Abajo están todos los partidos."
    html = f"""
    <html><body style="font-family:Arial; padding:20px; background:#f5f5f5;">
    <h1>⚽ Analizador Completo - {hoy} (Colombia)</h1>
    <h2>{alertas_html}</h2>
    <h3>Partidos hoy + mañana: {len(fixtures)}</h3>
    {lista_partidos}
    </body></html>
    """
    return html

@app.get("/")
def inicio():
    return {"mensaje": "Analizador prendido", "fecha_colombia": get_fecha_colombia()}
