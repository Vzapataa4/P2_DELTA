"""Esquemas Pydantic (validación de entrada/salida de la API)."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------- Auth ----------
class LoginRequest(BaseModel):
    correo: EmailStr
    contrasena: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    nombre: str
    rol: str


# ---------- Insumo ----------
class InsumoCreate(BaseModel):
    nombre: str = Field(min_length=1)
    unidad: str = "gr"
    cantidad_disponible: float = Field(ge=0)
    nivel_minimo: float = Field(ge=0, default=0)
    costo_unitario: float = Field(ge=0, default=0)
    proveedor_nombre: Optional[str] = None


class InsumoOut(BaseModel):
    id: int
    nombre: str
    unidad: str
    cantidad_disponible: float
    nivel_minimo: float
    costo_unitario: float
    bajo: bool
    nivel: str  # "ok" | "medio" | "bajo" -> ver Acta de Compromiso 5/ago/2026
    proveedor_nombre: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ---------- Receta ----------
class RecetaInsumoIn(BaseModel):
    insumo_nombre: str
    cantidad_requerida: float = Field(gt=0)


class RecetaCreate(BaseModel):
    nombre: str = Field(min_length=1)
    insumos: List[RecetaInsumoIn] = Field(min_length=1)
    precio_venta: Optional[float] = Field(default=None, ge=0)


class RecetaInsumoOut(BaseModel):
    insumo_nombre: str
    cantidad_requerida: float


class RecetaOut(BaseModel):
    id: int
    nombre: str
    insumos: List[RecetaInsumoOut]
    costo_total: float
    precio_venta: Optional[float] = None
    ganancia_unitaria: float

    model_config = ConfigDict(from_attributes=True)


# ---------- Importación de receta desde Excel ----------
class ExcelInsumoLineaOut(BaseModel):
    insumo_nombre: str
    cantidad_requerida: float
    existe: bool  # si el insumo ya está registrado en el inventario


class ExcelRecetaImportOut(BaseModel):
    receta_nombre: str
    lineas: List[ExcelInsumoLineaOut]
    mensaje: str


# ---------- Venta ----------
class VentaCreate(BaseModel):
    distribuidor_nombre: str = Field(min_length=1)
    receta_nombre: str = Field(min_length=1)
    cantidad: int = Field(gt=0)


class VentaOut(BaseModel):
    id: int
    fecha: datetime
    distribuidor_nombre: Optional[str]
    receta_nombre: str
    cantidad: int
    total: float


class VentaLoteLinea(BaseModel):
    receta_nombre: str = Field(min_length=1)
    cantidad: int = Field(gt=0)


class VentaLoteCreate(BaseModel):
    distribuidor_nombre: str = Field(min_length=1)
    lineas: List[VentaLoteLinea] = Field(min_length=1)


# ---------- Importación de venta desde foto de factura ----------
class FacturaLineaOut(BaseModel):
    receta_nombre: str
    cantidad: int


class FacturaImportOut(BaseModel):
    distribuidor_nombre: str
    lineas: List[FacturaLineaOut]
    fuente: str  # "ia" si se pudo leer la imagen, "manual" si no
    mensaje: str


# ---------- Dashboard ----------
class DashboardOut(BaseModel):
    ventas_hoy: int
    insumos_en_alerta: int
    recetas_registradas: int
    ventas_por_dia: List[dict]
    ventas_por_semana: List[dict]
    ventas_por_mes: List[dict]
    productos_mas_vendidos: List[dict]
    analisis_distribuidores: List[dict]


# ---------- IA ----------
class RecomendacionOut(BaseModel):
    insumo: str
    mensaje: str
    fuente: str  # "ia" o "regla" (fallback si la IA no respondió)
