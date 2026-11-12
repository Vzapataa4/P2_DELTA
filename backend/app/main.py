import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import auth, compras, dashboard, facturas, ia, insumos, recetas, ventas

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="La Amassadera Inteligente — API",
    description="Backend de La Amassadera Inteligente: inventario, compras, ventas, facturas, recetas, panel y recomendaciones de IA.",
    version="1.0.0",
)

# En producción ALLOWED_ORIGINS trae el dominio del frontend en Vercel
# (separados por coma si son varios). Sin la variable, se deja abierto para
# poder trabajar en local.
_origenes = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origenes or ["*"],
    allow_credentials=bool(_origenes),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(insumos.router)
app.include_router(recetas.router)
app.include_router(ventas.router)
app.include_router(dashboard.router)
app.include_router(ia.router)
app.include_router(compras.router)
app.include_router(facturas.router)


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}
