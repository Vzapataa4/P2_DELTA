import math
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import auth, ia, models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/ia", tags=["ia"])


@router.get("/recomendaciones", response_model=list[schemas.RecomendacionOut])
def recomendaciones(
    db: Session = Depends(get_db), _user: models.Usuario = Depends(auth.require_admin)
):
    """HU-19 Analizar consumo histórico + HU-20 Recomendar reabastecimiento.

    Si la API de Claude no está disponible, se degrada a una recomendación
    por regla en vez de fallar (ver Wiki_RNF_Ampliados.md)."""
    insumos_bajos = [i for i in db.query(models.Insumo).all() if i.bajo]
    return ia.generar_recomendaciones(insumos_bajos)


@router.get("/recetas-sugeridas", response_model=list[schemas.RecetaSugeridaOut])
def recetas_sugeridas(
    db: Session = Depends(get_db), _user: models.Usuario = Depends(auth.require_admin)
):
    """HU-21 Sugerir recetas a producir. Regla transparente (no requiere
    API externa): solo se sugieren recetas que el inventario actual
    permite producir; se priorizan las más vendidas en los últimos 30
    días y, a igual demanda, las de mayor ganancia unitaria."""
    desde = datetime.utcnow() - timedelta(days=30)
    vendidas = {}
    for v in db.query(models.Venta).filter(models.Venta.fecha >= desde).all():
        vendidas[v.receta_id] = vendidas.get(v.receta_id, 0) + v.cantidad

    sugeridas = []
    for r in db.query(models.Receta).all():
        if not r.insumos:
            continue
        posibles = [
            (math.floor(ri.insumo.cantidad_disponible / ri.cantidad_requerida), ri.insumo.nombre)
            for ri in r.insumos
        ]
        producibles, limitante = min(posibles)
        if producibles < 1:
            continue
        unidades = vendidas.get(r.id, 0)
        motivo = (
            f"Se vendieron {unidades} unidades en los últimos 30 días y el inventario alcanza "
            f"para {producibles} más (limita: {limitante})."
            if unidades
            else f"Sin ventas recientes, pero el inventario alcanza para {producibles} unidades (limita: {limitante})."
        )
        sugeridas.append(
            schemas.RecetaSugeridaOut(
                receta=r.nombre,
                unidades_producibles=producibles,
                insumo_limitante=limitante,
                unidades_vendidas_30d=unidades,
                ganancia_unitaria=round(r.ganancia_unitaria, 2),
                motivo=motivo,
                fuente="regla",
            )
        )
    return sorted(sugeridas, key=lambda s: (-s.unidades_vendidas_30d, -s.ganancia_unitaria, s.receta))
