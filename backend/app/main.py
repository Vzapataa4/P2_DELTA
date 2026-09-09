from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import auth, dashboard, ia, insumos, recetas, ventas

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="La Amassadera Inteligente — API",
    description="Backend del MVP de Sprint 1: inventario, ventas, recetas, panel y recomendaciones de IA.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # MVP local; en producción restringir al dominio del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(insumos.router)
app.include_router(recetas.router)
app.include_router(ventas.router)
app.include_router(dashboard.router)
app.include_router(ia.router)


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}
