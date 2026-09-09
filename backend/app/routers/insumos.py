from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/insumos", tags=["insumos"])


def _to_out(i: models.Insumo) -> schemas.InsumoOut:
    return schemas.InsumoOut(
        id=i.id,
        nombre=i.nombre,
        unidad=i.unidad,
        cantidad_disponible=i.cantidad_disponible,
        nivel_minimo=i.nivel_minimo,
        costo_unitario=i.costo_unitario,
        bajo=i.bajo,
        nivel=i.nivel,
        proveedor_nombre=i.proveedor.nombre if i.proveedor else None,
    )


@router.get("", response_model=list[schemas.InsumoOut])
def listar_insumos(
    db: Session = Depends(get_db), _user: models.Usuario = Depends(auth.get_current_user)
):
    """HU-04 Ver inventario actual. Disponible para cualquier usuario autenticado
    (dueño o empleado) — ver Wiki_RNF_Ampliados.md, HU-08."""
    return [_to_out(i) for i in db.query(models.Insumo).order_by(models.Insumo.nombre).all()]


@router.post("", response_model=schemas.InsumoOut, status_code=201)
def registrar_insumo(
    data: schemas.InsumoCreate,
    db: Session = Depends(get_db),
    _user: models.Usuario = Depends(auth.require_admin),
):
    """HU-03 Registrar insumos. Solo administrador."""
    existente = db.query(models.Insumo).filter(models.Insumo.nombre.ilike(data.nombre)).first()
    if existente:
        raise HTTPException(status_code=409, detail="Ese insumo ya existe")

    proveedor = None
    if data.proveedor_nombre:
        proveedor = (
            db.query(models.Proveedor)
            .filter(models.Proveedor.nombre.ilike(data.proveedor_nombre))
            .first()
        )
        if not proveedor:
            proveedor = models.Proveedor(nombre=data.proveedor_nombre)
            db.add(proveedor)
            db.flush()

    insumo = models.Insumo(
        nombre=data.nombre,
        unidad=data.unidad,
        cantidad_disponible=data.cantidad_disponible,
        nivel_minimo=data.nivel_minimo,
        costo_unitario=data.costo_unitario,
        proveedor_id=proveedor.id if proveedor else None,
    )
    db.add(insumo)
    db.commit()
    db.refresh(insumo)
    return _to_out(insumo)
