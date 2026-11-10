from fastapi import FastAPI
import requests
import os

app = FastAPI(title="Analizador Deportivo")

API_KEY = os.getenv("API_KEY")
HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://v3.football.api-sports.io"

@app.get("/")
def inicio():
    return {"mensaje": "Analizador Deportivo"}

@app.get("/health")
def verificar_estado():
    return {"estado": "OK"}

@app.get("/partidos-hoy")
def partidos_hoy():
    url = f"{BASE_URL}/fixtures?date=2026-11-09"
    r = requests.get(url, headers=HEADERS)
    partidos = []
    for p in r.json()["response"]:
        partidos.append({"local": p["teams"]["home"]["name"], "visitante": p["teams"]["away"]["name"]})
    return partidos
