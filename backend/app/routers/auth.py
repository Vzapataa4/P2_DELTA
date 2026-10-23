from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=schemas.LoginResponse)
def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.Usuario).filter(models.Usuario.correo == data.correo).first()
    if not user or not auth.verify_password(data.contrasena, user.contrasena_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
        )
    token = auth.create_access_token({"sub": user.correo})
    return schemas.LoginResponse(access_token=token, nombre=user.nombre, rol=user.rol.value)


@router.post("/empleados", response_model=schemas.UsuarioOut, status_code=201)
def crear_empleado(
    data: schemas.EmpleadoCreate,
    db: Session = Depends(get_db),
    _admin: models.Usuario = Depends(auth.require_admin),
):
    """HU-02 Crear cuenta de empleado. Solo el administrador puede crear
    cuentas; el rol siempre es "empleado" (no se puede crear otro admin
    desde la API, para no escalar privilegios)."""
    if db.query(models.Usuario).filter(models.Usuario.correo == data.correo).first():
        raise HTTPException(status_code=409, detail="Ya existe un usuario con ese correo")
    user = models.Usuario(
        nombre=data.nombre,
        correo=data.correo,
        contrasena_hash=auth.hash_password(data.contrasena),
        rol=models.RolUsuario.EMPLEADO,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return schemas.UsuarioOut(id=user.id, nombre=user.nombre, correo=user.correo, rol=user.rol.value)


@router.get("/usuarios", response_model=list[schemas.UsuarioOut])
def listar_usuarios(
    db: Session = Depends(get_db), _admin: models.Usuario = Depends(auth.require_admin)
):
    return [
        schemas.UsuarioOut(id=u.id, nombre=u.nombre, correo=u.correo, rol=u.rol.value)
        for u in db.query(models.Usuario).order_by(models.Usuario.nombre).all()
    ]
