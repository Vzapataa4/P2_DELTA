from collections import defaultdict
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=schemas.DashboardOut)
def panel_principal(
    db: Session = Depends(get_db), _user: models.Usuario = Depends(auth.require_admin)
):
    """HU-16 Ver panel principal: resumen agregado de ventas, alertas y
    recetas. Incluye vista diaria (pedida en el Acta de Compromiso del 5
    de agosto de 2026), semanal y mensual, más el análisis por
    distribuidor pedido en la misma acta."""
    hoy = datetime.utcnow().date()
    ventas = db.query(models.Venta).all()
    ventas_hoy = [v for v in ventas if v.fecha.date() == hoy]

    insumos = db.query(models.Insumo).all()
    insumos_en_alerta = sum(1 for i in insumos if i.bajo)
    recetas_registradas = db.query(models.Receta).count()

    por_dia = defaultdict(float)
    por_semana = defaultdict(float)
    por_mes = defaultdict(float)
    for v in ventas:
        por_dia[v.fecha.strftime("%Y-%m-%d")] += v.total
        anio, semana, _ = v.fecha.isocalendar()
        por_semana[f"{anio}-W{semana:02d}"] += v.total
        por_mes[v.fecha.strftime("%Y-%m")] += v.total
    ventas_por_dia = [{"dia": k, "total": v} for k, v in sorted(por_dia.items())]
    ventas_por_semana = [{"semana": k, "total": v} for k, v in sorted(por_semana.items())]
    ventas_por_mes = [{"mes": k, "total": v} for k, v in sorted(por_mes.items())]

    por_producto = defaultdict(int)
    for v in ventas:
        por_producto[v.receta.nombre] += v.cantidad
    total_unidades = sum(por_producto.values()) or 1
    productos_mas_vendidos = sorted(
        (
            {"producto": k, "pct": round(v / total_unidades * 100, 1)}
            for k, v in por_producto.items()
        ),
        key=lambda x: -x["pct"],
    )

    # Análisis por distribuidor (Acta de Compromiso, 5/ago/2026): producto
    # que más se vende y ganancia generada por cada distribuidor. La
    # "ganancia" es el total vendido menos el costo de los insumos
    # consumidos (Receta.costo_total) -- todavía no existe un módulo
    # separado de gastos generales del negocio, así que esto es lo que hoy
    # se puede calcular con los datos que ya registra el sistema.
    por_distribuidor = defaultdict(lambda: {"unidades": defaultdict(int), "ganancia": 0.0})
    for v in ventas:
        clave = v.distribuidor_nombre or "Sin distribuidor"
        por_distribuidor[clave]["unidades"][v.receta.nombre] += v.cantidad
        costo = v.receta.costo_total * v.cantidad
        por_distribuidor[clave]["ganancia"] += v.total - costo

    analisis_distribuidores = []
    for distribuidor, info in por_distribuidor.items():
        if not info["unidades"]:
            continue
        producto_top, unidades_top = max(info["unidades"].items(), key=lambda kv: kv[1])
        analisis_distribuidores.append(
            {
                "distribuidor": distribuidor,
                "producto_top": producto_top,
                "unidades_producto_top": unidades_top,
                "ganancia_total": round(info["ganancia"], 2),
            }
        )
    analisis_distribuidores.sort(key=lambda x: -x["ganancia_total"])

    return schemas.DashboardOut(
        ventas_hoy=len(ventas_hoy),
        insumos_en_alerta=insumos_en_alerta,
        recetas_registradas=recetas_registradas,
        ventas_por_dia=ventas_por_dia,
        ventas_por_semana=ventas_por_semana,
        ventas_por_mes=ventas_por_mes,
        productos_mas_vendidos=productos_mas_vendidos,
        analisis_distribuidores=analisis_distribuidores,
    )
