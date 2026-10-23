
from collections import defaultdict
from datetime import date, datetime, time
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import auth, importaciones, models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/ventas", tags=["ventas"])


@router.get("", response_model=list[schemas.VentaOut])
def listar_ventas(
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    distribuidor: Optional[str] = None,
    db: Session = Depends(get_db),
    _user: models.Usuario = Depends(auth.require_admin),
):
    """HU-11 Ver historial de ventas, con filtros opcionales por rango de
    fechas (desde/hasta, inclusivos) y por distribuidor."""
    if desde and hasta and desde > hasta:
        raise HTTPException(status_code=400, detail="La fecha 'desde' no puede ser posterior a 'hasta'")
    q = db.query(models.Venta)
    if desde:
        q = q.filter(models.Venta.fecha >= datetime.combine(desde, time.min))
    if hasta:
        q = q.filter(models.Venta.fecha <= datetime.combine(hasta, time.max))
    if distribuidor:
        q = q.filter(models.Venta.distribuidor_nombre.ilike(distribuidor))
    ventas = q.order_by(models.Venta.fecha.desc()).all()
    return [
        schemas.VentaOut(
            id=v.id,
            fecha=v.fecha,
            distribuidor_nombre=v.distribuidor_nombre,
            receta_nombre=v.receta.nombre,
            cantidad=v.cantidad,
            total=v.total,
        )
        for v in ventas
    ]


def _registrar_venta_interna(
    db: Session, distribuidor_nombre: str, receta_nombre: str, cantidad: int
) -> schemas.VentaOut:
    """HU-09 Registrar venta/pedido + HU-10 Descuento automático de insumos.

    Función compartida entre el registro individual y el registro en lote
    (usado por la importación de factura), para no duplicar la lógica de
    validación ni el manejo de fallos (ver Wiki_RNF_Ampliados.md)."""
    receta = (
        db.query(models.Receta)
        .filter(models.Receta.nombre.ilike(receta_nombre))
        .first()
    )
    if not receta:
        raise HTTPException(status_code=404, detail=f"La receta '{receta_nombre}' no existe")

    faltantes = []
    for ri in receta.insumos:
        requerido = ri.cantidad_requerida * cantidad
        if ri.insumo.cantidad_disponible < requerido:
            faltantes.append(ri.insumo.nombre)
    if faltantes:
        raise HTTPException(
            status_code=400,
            detail=f"Insumo insuficiente para registrar la venta de {receta_nombre}: {', '.join(faltantes)}",
        )

    try:
        for ri in receta.insumos:
            ri.insumo.cantidad_disponible -= ri.cantidad_requerida * cantidad

        total = receta.precio_venta_efectivo * cantidad
        venta = models.Venta(
            distribuidor_nombre=distribuidor_nombre,
            receta_id=receta.id,
            cantidad=cantidad,
            total=total,
        )
        db.add(venta)
        db.commit()
        db.refresh(venta)
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="No se pudo registrar la venta. No se modificó el inventario.",
        )

    return schemas.VentaOut(
        id=venta.id,
        fecha=venta.fecha,
        distribuidor_nombre=venta.distribuidor_nombre,
        receta_nombre=receta.nombre,
        cantidad=venta.cantidad,
        total=venta.total,
    )


@router.post("", response_model=schemas.VentaOut, status_code=201)
def registrar_venta(
    data: schemas.VentaCreate,
    db: Session = Depends(get_db),
    _user: models.Usuario = Depends(auth.require_admin),
):
    return _registrar_venta_interna(db, data.distribuidor_nombre, data.receta_nombre, data.cantidad)


@router.post("/lote", response_model=list[schemas.VentaOut], status_code=201)
def registrar_ventas_lote(
    data: schemas.VentaLoteCreate,
    db: Session = Depends(get_db),
    _user: models.Usuario = Depends(auth.require_admin),
):
    """Registra varias líneas de producto de un mismo distribuidor en una
    sola operación (ej. una factura con varios panes). Se usa junto con
    /importar-factura: primero se sugieren las líneas leyendo la foto, y
    luego el usuario las confirma y las envía aquí."""
    return [
        _registrar_venta_interna(db, data.distribuidor_nombre, linea.receta_nombre, linea.cantidad)
        for linea in data.lineas
    ]


@router.post("/importar-factura", response_model=schemas.FacturaImportOut)
async def importar_factura(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _user: models.Usuario = Depends(auth.require_admin),
):
    """Mejora pedida en el Acta de Compromiso (5 de agosto de 2026): subir
    una foto de factura para pre-llenar el registro de venta. Nunca
    registra la venta directamente -- el usuario siempre confirma/corrige
    primero (ver app/importaciones.py)."""
    contenido = await file.read()
    recetas_conocidas = [r.nombre for r in db.query(models.Receta).all()]
    return importaciones.extraer_factura_desde_imagen(contenido, file.content_type, recetas_conocidas)


@router.get("/ranking", response_model=list[schemas.RankingProductoOut])
def ranking_productos(
    limite: int = 10,
    db: Session = Depends(get_db),
    _user: models.Usuario = Depends(auth.require_admin),
):
    """HU-17 Ranking de productos: los más vendidos por unidades (el
    desempate es por ingresos)."""
    if limite < 1 or limite > 50:
        raise HTTPException(status_code=400, detail="El límite debe estar entre 1 y 50")
    unidades = defaultdict(int)
    ingresos = defaultdict(float)
    for v in db.query(models.Venta).all():
        unidades[v.receta.nombre] += v.cantidad
        ingresos[v.receta.nombre] += v.total
    ordenado = sorted(unidades, key=lambda n: (-unidades[n], -ingresos[n], n))[:limite]
    return [
        schemas.RankingProductoOut(
            posicion=i, producto=n, unidades=unidades[n], ingresos=round(ingresos[n], 2)
        )
        for i, n in enumerate(ordenado, start=1)
    ]
