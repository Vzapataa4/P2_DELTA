from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import auth, importaciones, models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/recetas", tags=["recetas"])


def _to_out(r: models.Receta) -> schemas.RecetaOut:
    return schemas.RecetaOut(
        id=r.id,
        nombre=r.nombre,
        insumos=[
            schemas.RecetaInsumoOut(
                insumo_nombre=ri.insumo.nombre, cantidad_requerida=ri.cantidad_requerida
            )
            for ri in r.insumos
        ],
        costo_total=r.costo_total,
        precio_venta=r.precio_venta,
        ganancia_unitaria=r.ganancia_unitaria,
    )


@router.get("/rentabilidad", response_model=list[schemas.RentabilidadOut])
def rentabilidad_por_producto(
    db: Session = Depends(get_db), _user: models.Usuario = Depends(auth.require_admin)
):
    """HU-15 Ver rentabilidad por producto: costo, precio, ganancia y
    margen unitarios, más la ganancia acumulada según lo ya vendido."""
    vendidas = {}
    for v in db.query(models.Venta).all():
        vendidas[v.receta_id] = vendidas.get(v.receta_id, 0) + v.cantidad
    filas = []
    for r in db.query(models.Receta).all():
        costo = r.costo_total
        precio = r.precio_venta_efectivo
        ganancia = precio - costo
        unidades = vendidas.get(r.id, 0)
        filas.append(
            schemas.RentabilidadOut(
                receta=r.nombre,
                costo_unitario=round(costo, 2),
                precio_venta=round(precio, 2),
                ganancia_unitaria=round(ganancia, 2),
                margen_pct=round(ganancia / precio * 100, 1) if precio else 0.0,
                unidades_vendidas=unidades,
                ganancia_total=round(ganancia * unidades, 2),
            )
        )
    return sorted(filas, key=lambda f: (-f.margen_pct, f.receta))


@router.get("", response_model=list[schemas.RecetaOut])
def listar_recetas(
    db: Session = Depends(get_db), _user: models.Usuario = Depends(auth.get_current_user)
):
    """HU-14 Calcular costo de receta (el costo se calcula al vuelo, ver
    Receta.costo_total en app/models.py)."""
    return [_to_out(r) for r in db.query(models.Receta).order_by(models.Receta.nombre).all()]


@router.post("", response_model=schemas.RecetaOut, status_code=201)
def registrar_receta(
    data: schemas.RecetaCreate,
    db: Session = Depends(get_db),
    _user: models.Usuario = Depends(auth.require_admin),
):
    """HU-13 Registrar receta. Solo administrador."""
    existente = db.query(models.Receta).filter(models.Receta.nombre.ilike(data.nombre)).first()
    if existente:
        raise HTTPException(status_code=409, detail="Ya existe una receta con ese nombre")

    receta = models.Receta(nombre=data.nombre, precio_venta=data.precio_venta)
    db.add(receta)
    db.flush()

    for linea in data.insumos:
        insumo = (
            db.query(models.Insumo)
            .filter(models.Insumo.nombre.ilike(linea.insumo_nombre))
            .first()
        )
        if not insumo:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"El insumo '{linea.insumo_nombre}' no existe. Regístralo primero.",
            )
        db.add(
            models.RecetaInsumo(
                receta_id=receta.id,
                insumo_id=insumo.id,
                cantidad_requerida=linea.cantidad_requerida,
            )
        )

    db.commit()
    db.refresh(receta)
    return _to_out(receta)


@router.post("/importar-excel", response_model=schemas.ExcelRecetaImportOut)
async def importar_excel_receta(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _user: models.Usuario = Depends(auth.require_admin),
):
    """Corrige el bug detectado en Sprint 0: un Excel de receta puede traer
    un nombre interno distinto al esperado, así que esto solo pre-llena el
    formulario -- el usuario confirma o corrige antes de guardar con
    POST /api/recetas (ver app/importaciones.py)."""
    contenido = await file.read()
    return importaciones.leer_excel_receta(contenido, file.filename or "", db)
