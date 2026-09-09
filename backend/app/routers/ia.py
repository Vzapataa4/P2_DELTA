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
