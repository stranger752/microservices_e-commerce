from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import models, schemas
from app.database import get_db
from typing import List, Optional
import logging
from datetime import timedelta
from app.utils import security

router = APIRouter(
    prefix="/empleado",
    tags=["empleado"],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": schemas.ErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": schemas.ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": schemas.ErrorResponse}
    }
)

logger = logging.getLogger(__name__)

def handle_db_error(e: Exception, operation: str):
    logger.error(f"Error during {operation}: {str(e)}", exc_info=True)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "error": "database_error",
            "message": f"Error al {operation} en la base de datos",
            "details": {"internal_error": str(e)}
        }
    )

@router.get(
    "/", 
    response_model=List[schemas.Empleado],
    summary="Obtener todos los empleados",
    description="Obtiene una lista paginada de todos los empleados registrados en el sistema.",
    response_description="Lista de empleados obtenida correctamente",
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al obtener la lista de empleados"
        }
    }
)
def get_employees(
    skip: int = Query(
        0, 
        ge=0, 
        description="Número de registros a omitir para paginación", 
        example=0
    ),
    limit: int = Query(
        100, 
        ge=1, 
        le=1000, 
        description="Número máximo de registros a retornar", 
        example=50
    ),
    db: Session = Depends(get_db)
):
    """
    Recupera una lista paginada de todos los empleados registrados.

    Parámetros:
        skip (int): Número de registros a omitir (para paginación).
        limit (int): Número máximo de registros a retornar.
        db (Session): Sesión de base de datos inyectada por dependencia.

    Retorna:
        List[Empleado]: Lista de objetos Empleado con sus datos básicos.
    """
    try:
        empleados = db.query(models.Empleado).offset(skip).limit(limit).all()
        return [
            schemas.Empleado(
                empleado_id=e.empleado_id,
                nombre=e.nombre,
                apellido1=e.apellido1,
                apellido2=e.apellido2,
                telefono=e.telefono,
                email=e.email,
                puesto=e.puesto,
                area=e.area
            )
            for e in empleados
        ]
    except Exception as e:
        handle_db_error(e, "obtener empleados")

@router.post(
    "/", 
    response_model=schemas.Empleado,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo empleado",
    description="Registra un nuevo empleado en el sistema con la información proporcionada.",
    response_description="Empleado creado exitosamente",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": schemas.ErrorResponse,
            "description": "Datos de entrada inválidos o incompletos"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al crear el empleado"
        }
    }
)
def create_employee(
    empleado: schemas.EmpleadoCreate, 
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo registro de empleado en la base de datos.

    Parámetros:
        empleado (EmpleadoCreate): Objeto con los datos del empleado a crear.
        db (Session): Sesión de base de datos inyectada por dependencia.

    Retorna:
        Empleado: Objeto con los datos del empleado creado, incluyendo su ID generado.
    """
    try:
        hashed_password = security.get_password_hash(empleado.contrasena)
        db_empleado = models.Empleado(
            **empleado.dict(exclude={"contrasena"}),
            contrasena=hashed_password
        )
        db.add(db_empleado)
        db.commit()
        db.refresh(db_empleado)
        return schemas.Empleado(
            empleado_id=db_empleado.empleado_id,
            nombre=db_empleado.nombre,
            apellido1=db_empleado.apellido1,
            apellido2=db_empleado.apellido2,
            telefono=db_empleado.telefono,
            email=db_empleado.email,
            puesto=db_empleado.puesto,
            area=db_empleado.area
        )
    except Exception as e:
        db.rollback()
        handle_db_error(e, "crear empleado")

@router.get(
    "/{empleado_id}", 
    response_model=schemas.Empleado,
    summary="Obtener un empleado por ID",
    description="Recupera los detalles completos de un empleado específico usando su ID único.",
    response_description="Detalles del empleado encontrado",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.ErrorResponse,
            "description": "No se encontró un empleado con el ID especificado"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al obtener el empleado"
        }
    }
)
def get_employee(
    empleado_id: int, 
    db: Session = Depends(get_db)
):
    """
    Obtiene los detalles de un empleado específico por su ID.

    Parámetros:
        empleado_id (int): ID único del empleado a consultar.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        Empleado: Objeto con todos los datos del empleado solicitado.

    Excepciones:
        HTTPException 404: Si no se encuentra el empleado con el ID especificado.
    """
    try:
        db_empleado = db.query(models.Empleado).filter(models.Empleado.empleado_id == empleado_id).first()
        if not db_empleado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "message": f"Empleado con ID {empleado_id} no encontrado",
                    "details": {"empleado_id": empleado_id}
                }
            )
        return schemas.Empleado(
            empleado_id=db_empleado.empleado_id,
            nombre=db_empleado.nombre,
            apellido1=db_empleado.apellido1,
            apellido2=db_empleado.apellido2,
            telefono=db_empleado.telefono,
            email=db_empleado.email,
            puesto=db_empleado.puesto,
            area=db_empleado.area
        )
    except Exception as e:
        handle_db_error(e, "obtener empleado")

@router.put(
    "/{empleado_id}", 
    response_model=schemas.Empleado,
    summary="Actualizar un empleado",
    description="Actualiza uno o más campos de un empleado existente utilizando su ID. No es necesario enviar todos los campos.",
    response_description="Empleado actualizado exitosamente.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.ErrorResponse,
            "description": "No se encontró el empleado a actualizar."
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": schemas.ErrorResponse,
            "description": "Datos de entrada inválidos."
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al actualizar el empleado."
        }
    }
)
def update_employee(
    empleado_id: int,
    empleado: schemas.EmpleadoUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza parcial o totalmente un empleado existente.

    Solo se modificarán los campos que sean enviados en el cuerpo de la solicitud.

    Parámetros:
        empleado_id (int): ID del empleado a actualizar.
        empleado (EmpleadoUpdate): Datos opcionales del empleado a actualizar.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        Empleado: Representación del empleado actualizado.
    """
    try:
        db_empleado = db.query(models.Empleado).filter(models.Empleado.empleado_id == empleado_id).first()
        if not db_empleado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "message": f"Empleado con ID {empleado_id} no encontrado",
                    "details": {"empleado_id": empleado_id}
                }
            )
        
        update_data = empleado.dict(exclude_unset=True)
        
        if "contrasena" in update_data:
            update_data["contrasena"] = security.get_password_hash(update_data["contrasena"])
        
        for field, value in update_data.items():
            setattr(db_empleado, field, value)
        
        db.commit()
        db.refresh(db_empleado)
        return schemas.Empleado(
            empleado_id=db_empleado.empleado_id,
            nombre=db_empleado.nombre,
            apellido1=db_empleado.apellido1,
            apellido2=db_empleado.apellido2,
            telefono=db_empleado.telefono,
            email=db_empleado.email,
            puesto=db_empleado.puesto,
            area=db_empleado.area
        )
    except Exception as e:
        db.rollback()
        handle_db_error(e, "actualizar parcialmente empleado")

@router.delete(
    "/{empleado_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un empleado",
    description="Elimina permanentemente un empleado del sistema usando su ID.",
    response_description="Empleado eliminado exitosamente",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.ErrorResponse,
            "description": "No se encontró el empleado a eliminar"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al eliminar el empleado"
        }
    }
)
def delete_employee(
    empleado_id: int, 
    db: Session = Depends(get_db)
):
    """
    Elimina un empleado de la base de datos.

    Parámetros:
        empleado_id (int): ID del empleado a eliminar.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        None: Código de estado 204 (No Content) si la eliminación fue exitosa.

    Excepciones:
        HTTPException 404: Si no se encuentra el empleado con el ID especificado.
    """
    try:
        db_empleado = db.query(models.Empleado).filter(models.Empleado.empleado_id == empleado_id).first()
        if not db_empleado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "message": f"Empleado con ID {empleado_id} no encontrado",
                    "details": {"empleado_id": empleado_id}
                }
            )
        
        db.delete(db_empleado)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        handle_db_error(e, "eliminar empleado")

@router.get(
    "", 
    response_model=List[schemas.Empleado],
    summary="Buscar empleados con filtros",
    description="Permite buscar empleados aplicando múltiples filtros opcionales.",
    response_description="Lista de empleados que coinciden con los criterios de búsqueda",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": schemas.ErrorResponse,
            "description": "Parámetros de búsqueda inválidos"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al realizar la búsqueda"
        }
    }
)
def search_employees(
    nombre: Optional[str] = Query(
        None, 
        min_length=2, 
        max_length=100,
        description="Filtrar por coincidencia parcial en el nombre"
    ),
    apellido1: Optional[str] = Query(
        None, 
        min_length=2, 
        max_length=50,
        description="Filtrar por coincidencia parcial en el primer apellido"
    ),
    apellido2: Optional[str] = Query(
        None, 
        min_length=2, 
        max_length=50,
        description="Filtrar por coincidencia parcial en el segundo apellido"
    ),
    email: Optional[str] = Query(
        None, 
        min_length=3, 
        max_length=100,
        description="Filtrar por coincidencia parcial en el email"
    ),
    puesto: Optional[schemas.Puesto] = Query(
        None,
        description="Filtrar por puesto específico del empleado"
    ),
    area: Optional[schemas.Area] = Query(
        None,
        description="Filtrar por área específica del empleado"
    ),
    skip: int = Query(
        0, 
        ge=0, 
        description="Número de registros a omitir", 
        example=0
    ),
    limit: int = Query(
        100, 
        ge=1, 
        le=500, 
        description="Número máximo de registros a retornar", 
        example=100
    ),
    db: Session = Depends(get_db)
):
    """
    Busca empleados aplicando filtros opcionales.

    Parámetros:
        nombre (str, opcional): Fragmento del nombre a buscar.
        apellido1 (str, opcional): Fragmento del primer apellido a buscar.
        apellido2 (str, opcional): Fragmento del segundo apellido a buscar.
        email (str, opcional): Fragmento del email a buscar.
        puesto (Puesto, opcional): Puesto específico del empleado.
        area (Area, opcional): Área específica del empleado.
        skip (int): Número de registros a omitir.
        limit (int): Número máximo de registros a retornar.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        List[Empleado]: Lista de empleados que coinciden con los filtros aplicados.
    """
    try:
        if all(param is None for param in [nombre, apellido1, apellido2, email, puesto, area]):
            return []

        query = db.query(models.Empleado)
        
        if nombre:
            query = query.filter(models.Empleado.nombre.ilike(f"%{nombre}%"))
        if apellido1:
            query = query.filter(models.Empleado.apellido1.ilike(f"%{apellido1}%"))
        if apellido2:
            query = query.filter(models.Empleado.apellido2.ilike(f"%{apellido2}%"))
        if email:
            query = query.filter(models.Empleado.email.ilike(f"%{email}%"))
        if puesto:
            query = query.filter(models.Empleado.puesto == puesto)
        if area:
            query = query.filter(models.Empleado.area == area)
        
        empleados = query.offset(skip).limit(limit).all()
        
        return [
            schemas.Empleado(
                empleado_id=e.empleado_id,
                nombre=e.nombre,
                apellido1=e.apellido1,
                apellido2=e.apellido2,
                telefono=e.telefono,
                email=e.email,
                puesto=e.puesto,
                area=e.area
            )
            for e in empleados
        ]
    except Exception as e:
        handle_db_error(e, "buscar empleados")

@router.post(
    "/login",
    summary="Iniciar sesión",
    description="Autentica a un empleado y genera un token de acceso JWT.",
    response_description="Token de acceso generado exitosamente",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": schemas.ErrorResponse,
            "description": "Credenciales inválidas"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al procesar la autenticación"
        }
    }
)
def login_for_access_token(
    credentials: schemas.TokenData, 
    db: Session = Depends(get_db)
):
    """
    Autentica a un empleado y genera un token JWT para acceso al sistema.

    Parámetros:
        credentials (TokenData): Objeto con credenciales (email y contraseña).
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        dict: Diccionario con el token de acceso y tipo de token.

    Excepciones:
        HTTPException 401: Si las credenciales son incorrectas.
    """
    try:
        empleado = db.query(models.Empleado).filter(models.Empleado.email == credentials.email).first()
        if not empleado or not security.verify_password(credentials.password, empleado.contrasena):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "invalid_credentials",
                    "message": "Credenciales incorrectas",
                    "details": None
                }
            )

        access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            data={"sub": empleado.email}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        handle_db_error(e, "iniciar sesión")