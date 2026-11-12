from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/facturas", tags=["facturas"])


def _to_out(f: models.Factura) -> schemas.FacturaOut:
    lineas = [
        schemas.FacturaLinea(
            producto=v.receta.nombre,
            cantidad=v.cantidad,
            precio_unitario=round(v.total / v.cantidad, 2) if v.cantidad else 0,
            subtotal=v.total,
        )
        for v in sorted(f.ventas, key=lambda v: v.id)
    ]
    return schemas.FacturaOut(
        id=f.id,
        numero=f.numero,
        fecha=f.fecha,
        distribuidor_nombre=f.distribuidor_nombre,
        lineas=lineas,
        total=f.total,
    )


@router.post("", response_model=schemas.FacturaOut, status_code=201)
def generar_factura(
    data: schemas.FacturaCreate,
    db: Session = Depends(get_db),
    _user: models.Usuario = Depends(auth.require_admin),
):
    """HU-12 Generar factura básica a partir de una o varias ventas ya
    registradas (las líneas de un pedido). Reglas: todas las ventas deben
    existir, ser del mismo distribuidor y no estar ya facturadas."""
    ids = sorted(set(data.venta_ids))
    ventas = db.query(models.Venta).filter(models.Venta.id.in_(ids)).all()
    if len(ventas) != len(ids):
        encontrados = {v.id for v in ventas}
        faltan = [str(i) for i in ids if i not in encontrados]
        raise HTTPException(status_code=404, detail=f"No existen las ventas: {', '.join(faltan)}")

    distribuidores = {(v.distribuidor_nombre or "").strip().lower() for v in ventas}
    if len(distribuidores) > 1:
        raise HTTPException(
            status_code=400,
            detail="Una factura solo puede tener ventas de un mismo distribuidor",
        )

    ya_facturadas = (
        db.query(models.factura_ventas.c.venta_id)
        .filter(models.factura_ventas.c.venta_id.in_(ids))
        .all()
    )
    if ya_facturadas:
        lista = ", ".join(str(fila[0]) for fila in ya_facturadas)
        raise HTTPException(status_code=409, detail=f"Estas ventas ya están facturadas: {lista}")

    factura = models.Factura(
        distribuidor_nombre=ventas[0].distribuidor_nombre or "Sin distribuidor",
        total=round(sum(v.total for v in ventas), 2),
        ventas=ventas,
    )
    db.add(factura)
    db.commit()
    db.refresh(factura)
    return _to_out(factura)


@router.get("", response_model=list[schemas.FacturaOut])
def listar_facturas(
    db: Session = Depends(get_db), _user: models.Usuario = Depends(auth.require_admin)
):
    return [_to_out(f) for f in db.query(models.Factura).order_by(models.Factura.id.desc()).all()]


@router.get("/ventas-facturadas", response_model=list[int])
def ventas_facturadas(
    db: Session = Depends(get_db), _user: models.Usuario = Depends(auth.require_admin)
):
    """Ids de ventas que ya tienen factura (el historial las marca así)."""
    return [fila[0] for fila in db.query(models.factura_ventas.c.venta_id).all()]


@router.get("/{factura_id}", response_model=schemas.FacturaOut)
def ver_factura(
    factura_id: int,
    db: Session = Depends(get_db),
    _user: models.Usuario = Depends(auth.require_admin),
):
    factura = db.get(models.Factura, factura_id)
    if not factura:
        raise HTTPException(status_code=404, detail="La factura no existe")
    return _to_out(factura)
