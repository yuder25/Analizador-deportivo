from fastapi import FastAPI

app = FastAPI(
    title="Analizador Deportivo",
    description="Sistema de análisis deportivo",
    version="1.0"
)

@app.get("/")
def inicio():
    return {
        "mensaje": "Analizador Deportivo funcionando",
        "estado": "Activo"
    }

@app.get("/health")
def verificar_estado():
    return {"estado": "OK"}
