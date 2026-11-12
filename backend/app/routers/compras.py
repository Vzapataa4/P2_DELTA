from collections import defaultdict
from datetime import date, datetime, time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/compras", tags=["compras"])


def _to_out(c: models.Compra) -> schemas.CompraOut:
    return schemas.CompraOut(
        id=c.id,
        fecha=c.fecha,
        proveedor=c.proveedor.nombre,
        insumo=c.insumo.nombre,
        cantidad=c.cantidad,
        unidad=c.insumo.unidad,
        costo_total=c.costo_total,
    )


def _filtrar_fechas(q, desde: Optional[date], hasta: Optional[date]):
    if desde and hasta and desde > hasta:
        raise HTTPException(status_code=400, detail="La fecha 'desde' no puede ser posterior a 'hasta'")
    if desde:
        q = q.filter(models.Compra.fecha >= datetime.combine(desde, time.min))
    if hasta:
        q = q.filter(models.Compra.fecha <= datetime.combine(hasta, time.max))
    return q


@router.post("", response_model=schemas.CompraOut, status_code=201)
def registrar_compra(
    data: schemas.CompraCreate,
    db: Session = Depends(get_db),
    _user: models.Usuario = Depends(auth.require_admin),
):
    """HU-07: registra la compra de un insumo y la suma al inventario."""
    insumo = db.query(models.Insumo).filter(models.Insumo.nombre.ilike(data.insumo_nombre)).first()
    if not insumo:
        raise HTTPException(status_code=404, detail=f"El insumo '{data.insumo_nombre}' no existe")

    proveedor = insumo.proveedor
    if data.proveedor_nombre and data.proveedor_nombre.strip():
        nombre = data.proveedor_nombre.strip()
        proveedor = db.query(models.Proveedor).filter(models.Proveedor.nombre.ilike(nombre)).first()
        if not proveedor:
            proveedor = models.Proveedor(nombre=nombre)
            db.add(proveedor)
            db.flush()
    if proveedor is None:
        raise HTTPException(
            status_code=400,
            detail="Este insumo no tiene proveedor asignado; escribe a quién se le compró",
        )

    compra = models.Compra(
        proveedor_id=proveedor.id,
        insumo_id=insumo.id,
        cantidad=data.cantidad,
        costo_total=data.costo_total,
    )
    insumo.cantidad_disponible += data.cantidad
    db.add(compra)
    db.commit()
    db.refresh(compra)
    return _to_out(compra)


@router.get("", response_model=list[schemas.CompraOut])
def listar_compras(
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    proveedor: Optional[str] = None,
    db: Session = Depends(get_db),
    _user: models.Usuario = Depends(auth.require_admin),
):
    q = _filtrar_fechas(db.query(models.Compra), desde, hasta)
    if proveedor:
        q = q.join(models.Proveedor).filter(models.Proveedor.nombre.ilike(proveedor))
    return [_to_out(c) for c in q.order_by(models.Compra.fecha.desc()).all()]


@router.get("/por-proveedor", response_model=list[schemas.ComprasProveedorOut])
def compras_por_proveedor(
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    db: Session = Depends(get_db),
    _user: models.Usuario = Depends(auth.require_admin),
):
    """HU-07 Ver compras por proveedor: cuántas compras, cuánto se le ha
    pagado y qué insumos se le compran a cada uno. Ordenado de mayor a
    menor gasto."""
    resumen = defaultdict(lambda: {"n": 0, "total": 0.0, "insumos": set(), "ultima": None})
    for c in _filtrar_fechas(db.query(models.Compra), desde, hasta).all():
        r = resumen[c.proveedor.nombre]
        r["n"] += 1
        r["total"] += c.costo_total
        r["insumos"].add(c.insumo.nombre)
        if r["ultima"] is None or c.fecha > r["ultima"]:
            r["ultima"] = c.fecha
    filas = [
        schemas.ComprasProveedorOut(
            proveedor=nombre,
            numero_compras=r["n"],
            total_gastado=round(r["total"], 2),
            insumos=sorted(r["insumos"]),
            ultima_compra=r["ultima"],
        )
        for nombre, r in resumen.items()
    ]
    return sorted(filas, key=lambda f: (-f.total_gastado, f.proveedor))
