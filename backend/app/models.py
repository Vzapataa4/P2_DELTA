"""Modelos de dominio (ver Modelado_Dominio.png en la Wiki)."""
import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from .database import Base


class RolUsuario(str, enum.Enum):
    ADMIN = "administrador"
    EMPLEADO = "empleado"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    correo = Column(String, unique=True, nullable=False, index=True)
    contrasena_hash = Column(String, nullable=False)
    rol = Column(SAEnum(RolUsuario), nullable=False, default=RolUsuario.ADMIN)


class Proveedor(Base):
    __tablename__ = "proveedores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    contacto = Column(String, nullable=True)

    insumos = relationship("Insumo", back_populates="proveedor")


class Insumo(Base):
    __tablename__ = "insumos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False, unique=True, index=True)
    unidad = Column(String, nullable=False, default="gr")
    cantidad_disponible = Column(Float, nullable=False, default=0)
    nivel_minimo = Column(Float, nullable=False, default=0)
    costo_unitario = Column(Float, nullable=False, default=0)  # costo por unidad (gr/ml/unid)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=True)

    proveedor = relationship("Proveedor", back_populates="insumos")

    @property
    def bajo(self) -> bool:
        return self.cantidad_disponible < self.nivel_minimo

    @property
    def nivel(self) -> str:
        """Clasificacion en 3 niveles con color pedida por Mauricio en el
        Acta de Compromiso del 5 de agosto de 2026: ok (verde),
        medio (naranjado), bajo (rojo)."""
        if self.cantidad_disponible < self.nivel_minimo:
            return "bajo"
        if self.cantidad_disponible < self.nivel_minimo * 1.5:
            return "medio"
        return "ok"


class Receta(Base):
    __tablename__ = "recetas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False, unique=True, index=True)
    # Precio al que se le vende al distribuidor. Es independiente del costo
    # (que se calcula solo, sumando los insumos): si no se define, se usa el
    # costo como precio -> la ganancia da 0 hasta que el dueño defina un
    # precio real de venta.
    precio_venta = Column(Float, nullable=True)

    insumos = relationship("RecetaInsumo", back_populates="receta", cascade="all, delete-orphan")

    @property
    def costo_total(self) -> float:
        return sum(ri.cantidad_requerida * ri.insumo.costo_unitario for ri in self.insumos)

    @property
    def precio_venta_efectivo(self) -> float:
        return self.precio_venta if self.precio_venta is not None else self.costo_total

    @property
    def ganancia_unitaria(self) -> float:
        return self.precio_venta_efectivo - self.costo_total


class RecetaInsumo(Base):
    __tablename__ = "receta_insumos"

    id = Column(Integer, primary_key=True, index=True)
    receta_id = Column(Integer, ForeignKey("recetas.id"), nullable=False)
    insumo_id = Column(Integer, ForeignKey("insumos.id"), nullable=False)
    cantidad_requerida = Column(Float, nullable=False)  # por unidad de producto vendida

    receta = relationship("Receta", back_populates="insumos")
    insumo = relationship("Insumo")


class Distribuidor(Base):
    __tablename__ = "distribuidores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    contacto = Column(String, nullable=True)


class Venta(Base):
    __tablename__ = "ventas"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime, default=datetime.utcnow)
    distribuidor_id = Column(Integer, ForeignKey("distribuidores.id"), nullable=True)
    distribuidor_nombre = Column(String, nullable=True)  # denormalizado por simplicidad del MVP
    receta_id = Column(Integer, ForeignKey("recetas.id"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    total = Column(Float, nullable=False, default=0)

    receta = relationship("Receta")
