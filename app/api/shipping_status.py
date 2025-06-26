from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.models import models, schemas
from app.database import get_db
from typing import List, Optional
from datetime import datetime
import logging

router = APIRouter(
    prefix="/estado_envio",
    tags=["estado_envio"],
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
    response_model=List[schemas.EstadoEnvio],
    summary="Obtener todos los estados de envío",
    description="Obtiene una lista paginada de todos los estados de envío registrados en el sistema.",
    response_description="Lista de estados de envío obtenida correctamente",
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al obtener la lista de estados de envío"
        }
    }
)
def get_shipping_statuses(
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
        example=100
    ),
    db: Session = Depends(get_db)
):
    """
    Recupera una lista paginada de todos los estados de envío registrados.

    Parámetros:
        skip (int): Número de registros a omitir.
        limit (int): Límite de registros a retornar.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        List[EstadoEnvio]: Lista de objetos EstadoEnvio con sus datos básicos.
    """
    try:
        estados = db.query(models.EstadoEnvio).offset(skip).limit(limit).all()
        return [
            schemas.EstadoEnvio(
                estado_envio_id=e.estado_envio_id,
                envio_id=e.envio_id,
                estado=e.estado,
                descripcion=e.descripcion,
                fecha=e.fecha,
                empleado_id=e.empleado_id
            )
            for e in estados
        ]
    except Exception as e:
        handle_db_error(e, "obtener estados de envío")

@router.post(
    "/", 
    response_model=schemas.EstadoEnvio,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo estado de envío",
    description="Registra un nuevo estado para un envío existente en el sistema.",
    response_description="Detalles del estado de envío creado",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": schemas.ErrorResponse,
            "description": "Datos de entrada inválidos o incompletos"
        },
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.ErrorResponse,
            "description": "No se encontró el envío o empleado asociado"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al crear el estado de envío"
        }
    }
)
def create_shipping_status(
    estado: schemas.EstadoEnvioCreate, 
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo registro de estado para un envío existente.

    Parámetros:
        estado (EstadoEnvioCreate): Objeto con los datos del estado a crear.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        EstadoEnvio: Objeto con los datos del estado creado, incluyendo su ID generado.

    Excepciones:
        HTTPException 404: Si no se encuentra el envío o empleado asociado.
    """
    try:
        envio = db.query(models.Envio).filter(models.Envio.envio_id == estado.envio_id).first()
        if not envio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "message": f"Envío con ID {estado.envio_id} no encontrado",
                    "details": {"envio_id": estado.envio_id}
                }
            )
        
        if estado.empleado_id:
            empleado = db.query(models.Empleado).filter(models.Empleado.empleado_id == estado.empleado_id).first()
            if not empleado:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": "not_found",
                        "message": f"Empleado con ID {estado.empleado_id} no encontrado",
                        "details": {"empleado_id": estado.empleado_id}
                    }
                )
        
        db_estado = models.EstadoEnvio(**estado.dict())
        db.add(db_estado)
        db.commit()
        db.refresh(db_estado)
        
        return schemas.EstadoEnvio(
            estado_envio_id=db_estado.estado_envio_id,
            envio_id=db_estado.envio_id,
            estado=db_estado.estado,
            descripcion=db_estado.descripcion,
            fecha=db_estado.fecha,
            empleado_id=db_estado.empleado_id
        )
    except Exception as e:
        db.rollback()
        handle_db_error(e, "crear estado de envío")

@router.get(
    "/{estado_envio_id}", 
    response_model=schemas.EstadoEnvio,
    summary="Obtener un estado de envío por ID",
    description="Recupera los detalles completos de un estado de envío específico usando su ID único.",
    response_description="Detalles del estado de envío encontrado",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.ErrorResponse,
            "description": "No se encontró un estado de envío con el ID especificado"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al obtener el estado de envío"
        }
    }
)
def get_shipping_status(
    estado_envio_id: int, 
    db: Session = Depends(get_db)
):
    """
    Obtiene los detalles de un estado de envío específico por su ID.

    Parámetros:
        estado_envio_id (int): ID único del estado a consultar.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        EstadoEnvio: Objeto con todos los datos del estado solicitado.

    Excepciones:
        HTTPException 404: Si no se encuentra el estado con el ID especificado.
    """
    try:
        db_estado = db.query(models.EstadoEnvio).filter(models.EstadoEnvio.estado_envio_id == estado_envio_id).first()
        if not db_estado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "message": f"Estado de envío con ID {estado_envio_id} no encontrado",
                    "details": {"estado_envio_id": estado_envio_id}
                }
            )

        return schemas.EstadoEnvio(
            estado_envio_id=db_estado.estado_envio_id,
            envio_id=db_estado.envio_id,
            estado=db_estado.estado,
            descripcion=db_estado.descripcion,
            fecha=db_estado.fecha,
            empleado_id=db_estado.empleado_id
        )
    except Exception as e:
        handle_db_error(e, "obtener estado de envío")

@router.put(
    "/{estado_envio_id}", 
    response_model=schemas.EstadoEnvio,
    summary="Actualizar un estado de envío",
    description="Actualiza parcial o totalmente los datos de un estado de envío existente. Solo se modificarán los campos que sean enviados en el cuerpo de la solicitud.",
    response_description="Detalles del estado de envío actualizado",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.ErrorResponse,
            "description": "No se encontró el estado de envío a actualizar"
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": schemas.ErrorResponse,
            "description": "Datos de estado inválidos"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al actualizar el estado de envío"
        }
    }
)
def update_shipping_status(
    estado_envio_id: int,
    estado: schemas.EstadoEnvioUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza parcial o totalmente un estado de envío existente.

    Solo se modificarán los campos que sean enviados en el cuerpo de la solicitud.

    Parámetros:
        estado_envio_id (int): ID del estado de envío a actualizar.
        estado (EstadoEnvioUpdate): Campos opcionales con los datos a modificar.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        EstadoEnvio: Objeto con los datos actualizados del estado de envío.

    Excepciones:
        HTTPException 404: Si no se encuentra el estado o empleado asociado.
    """
    try:
        db_estado = db.query(models.EstadoEnvio).filter(models.EstadoEnvio.estado_envio_id == estado_envio_id).first()
        if not db_estado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "message": f"Estado de envío con ID {estado_envio_id} no encontrado",
                    "details": {"estado_envio_id": estado_envio_id}
                }
            )
        
        if estado.empleado_id:
            empleado = db.query(models.Empleado).filter(models.Empleado.empleado_id == estado.empleado_id).first()
            if not empleado:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": "not_found",
                        "message": f"Empleado con ID {estado.empleado_id} no encontrado",
                        "details": {"empleado_id": estado.empleado_id}
                    }
                )

        update_data = estado.dict(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_estado, field, value)
        
        db.commit()
        db.refresh(db_estado)
        return schemas.EstadoEnvio(
            estado_envio_id=db_estado.estado_envio_id,
            envio_id=db_estado.envio_id,
            estado=db_estado.estado,
            descripcion=db_estado.descripcion,
            fecha=db_estado.fecha,
            empleado_id=db_estado.empleado_id
        )
    except Exception as e:
        db.rollback()
        handle_db_error(e, "actualizar estado de envío")

@router.delete(
    "/{estado_envio_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un estado de envío",
    description="Elimina permanentemente un estado de envío del sistema.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.ErrorResponse,
            "description": "No se encontró el estado de envío a eliminar"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al eliminar el estado de envío"
        }
    }
)
def delete_shipping_status(
    estado_envio_id: int, 
    db: Session = Depends(get_db)
):
    """
    Elimina un estado de envío existente por su ID.

    Parámetros:
        estado_envio_id (int): ID del estado a eliminar.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        None: Código de estado 204 (No Content) si la eliminación fue exitosa.

    Excepciones:
        HTTPException 404: Si no se encuentra el estado con el ID especificado.
    """
    try:
        db_estado = db.query(models.EstadoEnvio).filter(models.EstadoEnvio.estado_envio_id == estado_envio_id).first()
        if not db_estado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "message": f"Estado de envío con ID {estado_envio_id} no encontrado",
                    "details": {"estado_envio_id": estado_envio_id}
                }
            )
        
        db.delete(db_estado)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        handle_db_error(e, "eliminar estado de envío")

@router.get(
    "", 
    response_model=List[schemas.EstadoEnvio],
    summary="Buscar estados de envío usando filtros",
    description="Permite buscar estados de envío aplicando múltiples filtros opcionales.",
    response_description="Lista de estados de envío que coinciden con los criterios de búsqueda",
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
def search_shipping_statuses(
    envio_id: Optional[int] = Query(
        None,
        description="ID del envío asociado al estado"
    ),
    estado: Optional[schemas.EstadoEnvioEstado] = Query(
        None,
        description="Estado específico del envío"
    ),
    empleado_id: Optional[int] = Query(
        None,
        description="ID del empleado asociado al estado"
    ),
    descripcion: Optional[str] = Query(
        None,
        min_length=2,
        max_length=500,
        description="Fragmento de texto a buscar en la descripción"
    ),
    fecha_desde: Optional[str] = Query(
        None, 
        description="Fecha mínima del estado (formato YYYY-MM-DD)"
    ),
    fecha_hasta: Optional[str] = Query(
        None, 
        description="Fecha máxima del estado (formato YYYY-MM-DD)"
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
    Busca estados de envío aplicando filtros opcionales.

    Parámetros:
        envio_id (int, opcional): ID del envío asociado.
        estado (EstadoEnvioEstado, opcional): Estado específico del envío.
        empleado_id (int, opcional): ID del empleado asociado.
        descripcion (str, opcional): Fragmento de texto en la descripción.
        fecha_desde (str, opcional): Fecha mínima del estado.
        fecha_hasta (str, opcional): Fecha máxima del estado.
        skip (int): Número de registros a omitir.
        limit (int): Número máximo de registros a retornar.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        List[EstadoEnvio]: Lista de estados que coinciden con los filtros aplicados.
    """
    try:
        if all(param is None for param in [envio_id, estado, empleado_id, descripcion, fecha_desde, fecha_hasta]):
            return []

        query = db.query(models.EstadoEnvio)
        
        if envio_id:
            query = query.filter(models.EstadoEnvio.envio_id == envio_id)
        if estado:
            query = query.filter(models.EstadoEnvio.estado == estado)
        if empleado_id:
            query = query.filter(models.EstadoEnvio.empleado_id == empleado_id)
        if descripcion:
            query = query.filter(models.EstadoEnvio.descripcion.ilike(f"%{descripcion}%"))
        if fecha_desde:
            query = query.filter(models.EstadoEnvio.fecha >= f"{fecha_desde} 00:00:00")
        if fecha_hasta:
            query = query.filter(models.EstadoEnvio.fecha <= f"{fecha_hasta} 23:59:59")
        
        estados = query.order_by(models.EstadoEnvio.fecha.desc()).offset(skip).limit(limit).all()
        return [
            schemas.EstadoEnvio(
                estado_envio_id=e.estado_envio_id,
                envio_id=e.envio_id,
                estado=e.estado,
                descripcion=e.descripcion,
                fecha=e.fecha,
                empleado_id=e.empleado_id
            )
            for e in estados
        ]
    except Exception as e:
        handle_db_error(e, "buscar estados de envío")
