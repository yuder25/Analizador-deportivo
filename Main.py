 from fastapi import FastAPI
import requests
import os

app = FastAPI(title="Analizador Deportivo", description="Sistema de análisis y probabilidades deportivas", version="1.0")

API_KEY = os.getenv("API_KEY")
HEADERS = {'x-apisports-key': API_KEY}
BASE = "https://v3.football.api-sports.io"

@app.get("/")
def inicio():
    return {"mensaje": "Analizador Deportivo funcionando", "estado": "Activo"}

@app.get("/health")
def verificar_estado():
    return {"estado": "OK"}

@app.get("/partidos-hoy")
def partidos_hoy():
    url = f"{BASE}/fixtures?date=2026-11-09"
    r = requests.get(url, headers=HEADERS).json()
    partidos = []
    for p in r['response']:
        partidos.append({"local": p['teams']['home']['name'], "visita": p['teams']['away']['name'], "liga": p['league']['name'], "hora": p['fixture']['date']})
    return partidos

@app.get("/pronostico/{local}/{visita}")
def pronostico(local: str, visita: str):
    def buscar(nombre):
        url = f"{BASE}/teams?search={nombre}"
        r = requests.get(url, headers=HEADERS).json()
        return r['response'][0]['team']['id']
    id_local = buscar(local)
    id_visita = buscar(visita)
    def stats(equipo_id):
        url = f"{BASE}/teams/statistics?league=262&season=2026&team={equipo_id}"
        return requests.get(url, headers=HEADERS).json()['response']
    s_local = stats(id_local)
    s_visita = stats(id_visita)
    goles_local = float(s_local['goals']['for']['average']['home'] or 0)
    goles_visita = float(s_visita['goals']['for']['average']['away'] or 0)
    total = goles_local + goles_visita
    if total < 2.2:
        pick = "UNDER 2.5 GOLES"
        prob = 72
    elif total > 2.8:
        pick = "OVER 2.5 GOLES"
        prob = 68
    else:
        pick = "AMBOS MARCAN / UNDER 3.5"
        prob = 60
    return {"partido": f"{local} vs {visita}", "goles_esperados": round(total, 2), "pronostico": pick, "probabilidad": f"{prob}%"}
