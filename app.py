from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import requests
import os
from datetime import date

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

def prob_desde_cuota(cuota):
    try:
        if cuota and float(cuota) > 0:
            return round(100 / float(cuota), 1)
    except:
        pass
    return 0

def get_odds(fixture_id):
    try:
        url = f"{BASE_URL}/odds?fixture={fixture_id}&bookmaker=8"
        r = requests.get(url, headers=HEADERS, timeout=15).json()
        return r.get("response", [])
    except:
        return []

def buscar_apuesta(odds_data, bet_id, valor_buscado):
    for book in odds_data:
        for bookmaker in book.get("bookmakers", []):
            for bet in bookmaker.get("bets", []):
                if bet.get("id") == bet_id:
                    for v in bet.get("values", []):
                        if valor_buscado.lower() in v.get("value", "").lower():
                            return prob_desde_cuota(v.get("odd"))
    return 0

def get_ultimos_5(team_id):
    try:
        url = f"{BASE_URL}/fixtures?team={team_id}&last=5&status=FT"
        r = requests.get(url, headers=HEADERS, timeout=15).json()
        return r.get("response", [])
    except:
        return []

def analizar_racha(team_id, team_name):
    partidos = get_ultimos_5(team_id)
    if len(partidos) < 3:
        return None
    total_goles = 0
    btts = 0
    for p in partidos:
        g_home = p["goals"]["home"]
        g_away = p["goals"]["away"]
        if g_home is None or g_away is None:
            continue
        total_goles += g_home + g_away
        if g_home > 0 and g_away > 0:
            btts += 1
    if btts >= 4:
        return f"🚨 ALERTA - {team_name}: {btts}/{len(partidos)} ultimos partidos AMBOS ANOTARON. Patron fuerte de BTTS SI"
    if total_goles / max(1, len(partidos)) >= 3.0:
        return f"🚨 ALERTA - {team_name}: Promedio {round(total_goles/len(partidos),1)} goles por partido en ultimos {len(partidos)}. Patron de MUCHOS GOLES"
    return None

@app.get("/analizador-completo", response_class=HTMLResponse)
def analizador_completo():
    hoy = date.today().isoformat()
    url = f"{BASE_URL}/fixtures?date={hoy}"
    r = requests.get(url, headers=HEADERS, timeout=20).json()
    fixtures = r.get("response", [])[:20]

    alertas = []
    tarjetas = ""

    for p in fixtures:
        fixture_id = p["fixture"]["id"]
        local = p["teams"]["home"]["name"]
        visita = p["teams"]["away"]["name"]
        hora = p["fixture"]["date"][11:16]
        local_id = p["teams"]["home"]["id"]
        visita_id = p["teams"]["away"]["id"]

        odds = get_odds(fixture_id)
        p_local = buscar_apuesta(odds, 1, "Home")
        p_empate = buscar_apuesta(odds, 1, "Draw")
        p_visita = buscar_apuesta(odds, 1, "Away")
        p_btts_si = buscar_apuesta(odds, 8, "Yes")
        p_over_corners = buscar_apuesta(odds, 12, "Over 8.5")
        if p_over_corners == 0:
            p_over_corners = buscar_apuesta(odds, 12, "Over 7.5")

        if p_local == 0:
            p_local, p_empate, p_visita = 38, 28, 34
        if p_btts_si == 0:
            p_btts_si = 55
        if p_over_corners == 0:
            p_over_corners = 60

        ganador = local if p_local >= p_visita else visita
        prob_ganador = max(p_local, p_visita)
        btts_txt = f"SI - {p_btts_si}%" if p_btts_si >= 50 else f"NO - {100-p_btts_si}%"
        corners_txt = f"Mas de 8.5 - {p_over_corners}%" if p_over_corners >= 50 else f"Menos de 8.5 - {100-p_over_corners}%"

        for tid, tname in [(local_id, local), (visita_id, visita)]:
            alerta = analizar_racha(tid, tname)
            if alerta and alerta not in alertas:
                alertas.append(alerta)

        tarjetas += f"""
        <div style="background:white;border-radius:15px;padding:15px;margin-bottom:12px;box-shadow:0 2px 8px #ddd">
          <b>⚽ {local} vs {visita} - {hora}</b><br><br>
          ✅ <b>Ganador mas probable:</b> {ganador} - {prob_ganador}%<br>
          <small>Local {p_local}% | Empate {p_empate}% | Visita {p_visita}%</small><br><br>
          ✅ <b>Ambos anotan:</b> {btts_txt}<br><br>
          ✅ <b>Corners:</b> {corners_txt}<br>
        </div>
        """

    alertas_html = "".join([f"<div style='background:#ff2d2d;color:white;padding:12px;border-radius:12px;margin-bottom:10px'><b>{a}</b></div>" for a in alertas])
    if not alertas_html:
        alertas_html = "<div style='background:#eee;padding:12px;border-radius:12px;margin-bottom:10px'>Sin alertas de racha 5/5 hoy. Usa las probabilidades de abajo.</div>"

    html = f"""
    <html><head><meta name='viewport' content='width=device-width, initial-scale=1'><title>Analizador</title></head>
    <body style="font-family:Arial;background:#f2f2f2;padding:12px">
      <h2>🎯 Analizador Completo - {hoy}</h2>
      {alertas_html}
      {tarjetas}
      <p style="font-size:12px;color:#888">Probabilidades desde cuotas (1/cuota). Ninguna apuesta es 100% segura, las alertas son patrones que se repiten.</p>
    </body></html>
    """
    return html

@app.get("/partidos-hoy")
def partidos_hoy():
    hoy = date.today().isoformat()
    url = f"{BASE_URL}/fixtures?date={hoy}"
    r = requests.get(url, headers=HEADERS)
    partidos = []
    for p in r.json().get("response", []):
        partidos.append({"local": p["teams"]["home"]["name"], "visita": p["teams"]["away"]["name"]})
    return partidos
