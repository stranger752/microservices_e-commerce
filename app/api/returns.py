from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import models, schemas
from app.database import get_db
from typing import List, Optional
from datetime import datetime
import logging

router = APIRouter(
    prefix="/devolucion",
    tags=["devolucion"],
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
    response_model=List[schemas.Devolucion],
    summary="Obtener todas las devoluciones",
    description="Obtiene una lista paginada de todas las devoluciones registradas en el sistema.",
    response_description="Lista de devoluciones obtenida correctamente",
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al obtener la lista de devoluciones"
        }
    }
)
def get_returns(
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
    Recupera una lista paginada de todas las devoluciones registradas.

    Parámetros:
        skip (int): Número de registros a omitir.
        limit (int): Límite de registros a retornar.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        List[Devolucion]: Lista de objetos Devolucion con sus datos básicos.
    """
    try:
        devoluciones = db.query(models.Devolucion).offset(skip).limit(limit).all()
        return [
            schemas.Devolucion(
                devolucion_id=d.devolucion_id,
                envio_id=d.envio_id,
                motivo=d.motivo,
                fecha=d.fecha,
                estado=d.estado
            )
            for d in devoluciones
        ]
    except Exception as e:
        handle_db_error(e, "obtener devoluciones")

@router.post(
    "/", 
    response_model=schemas.Devolucion,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva devolución",
    description="Registra una nueva devolución en el sistema asociada a un envío existente.",
    response_description="Detalles de la devolución creada",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": schemas.ErrorResponse,
            "description": "Datos de devolución inválidos o incompletos"
        },
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.ErrorResponse,
            "description": "No se encontró el envío asociado"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al crear la devolución"
        }
    }
)
def create_return(
    devolucion: schemas.DevolucionCreate, 
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo registro de devolución asociado a un envío.

    Parámetros:
        devolucion (DevolucionCreate): Objeto con los datos de la devolución a crear.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        Devolucion: Objeto con los datos de la devolución creada, incluyendo su ID generado.

    Excepciones:
        HTTPException 404: Si no se encuentra el envío asociado.
    """
    try:
        envio = db.query(models.Envio).filter(models.Envio.envio_id == devolucion.envio_id).first()
        if not envio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "message": f"Envío con ID {devolucion.envio_id} no encontrado",
                    "details": {"envio_id": devolucion.envio_id}
                }
            )
        
        db_devolucion = models.Devolucion(**devolucion.dict())
        db.add(db_devolucion)
        db.commit()
        db.refresh(db_devolucion)
        
        return schemas.Devolucion(
            devolucion_id=db_devolucion.devolucion_id,
            envio_id=db_devolucion.envio_id,
            motivo=db_devolucion.motivo,
            fecha=db_devolucion.fecha,
            estado=db_devolucion.estado
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        handle_db_error(e, "crear devolución")

@router.get(
    "/{devolucion_id}", 
    response_model=schemas.Devolucion,
    summary="Obtener una devolución por ID",
    description="Recupera los detalles completos de una devolución específica usando su ID único.",
    response_description="Detalles de la devolución encontrada",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.ErrorResponse,
            "description": "No se encontró una devolución con el ID especificado"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al obtener la devolución"
        }
    }
)
def get_return(
    devolucion_id: int, 
    db: Session = Depends(get_db)
):
    """
    Obtiene los detalles de una devolución específica por su ID.

    Parámetros:
        devolucion_id (int): ID único de la devolución a consultar.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        Devolucion: Objeto con todos los datos de la devolución solicitada.

    Excepciones:
        HTTPException 404: Si no se encuentra la devolución con el ID especificado.
    """
    try:
        db_devolucion = db.query(models.Devolucion).filter(models.Devolucion.devolucion_id == devolucion_id).first()
        if not db_devolucion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "message": f"Devolución con ID {devolucion_id} no encontrada",
                    "details": {"devolucion_id": devolucion_id}
                }
            )

        return schemas.Devolucion(
            devolucion_id=db_devolucion.devolucion_id,
            envio_id=db_devolucion.envio_id,
            motivo=db_devolucion.motivo,
            fecha=db_devolucion.fecha,
            estado=db_devolucion.estado
        )
    except Exception as e:
        handle_db_error(e, "obtener devolución")

@router.put(
    "/{devolucion_id}", 
    response_model=schemas.Devolucion,
    summary="Actualizar una devolución",
    description="Actualiza uno o más campos de una devolución existente utilizando su ID. No es necesario enviar todos los campos.",
    response_description="Detalles de la devolución actualizada",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.ErrorResponse,
            "description": "No se encontró la devolución a actualizar o el envío asociado"
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": schemas.ErrorResponse,
            "description": "Datos de devolución inválidos"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al actualizar la devolución"
        }
    }
)
def update_return(
    devolucion_id: int,
    devolucion: schemas.DevolucionUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza parcial o totalmente los datos de una devolución existente.

    Solo se modificarán los campos que se incluyan en el cuerpo de la solicitud.

    Parámetros:
        devolucion_id (int): ID de la devolución a actualizar.
        devolucion (DevolucionUpdate): Campos opcionales de la devolución a modificar.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        Devolucion: Objeto con los datos actualizados de la devolución.

    Excepciones:
        HTTPException 404: Si no se encuentra la devolución o el envío asociado.
        HTTPException 400: Si los datos proporcionados son inválidos.
    """
    try:
        db_devolucion = db.query(models.Devolucion).filter(models.Devolucion.devolucion_id == devolucion_id).first()
        if not db_devolucion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "message": f"Devolución con ID {devolucion_id} no encontrada",
                    "details": {"devolucion_id": devolucion_id}
                }
            )
        
        if devolucion.envio_id and devolucion.envio_id != db_devolucion.envio_id:
            envio = db.query(models.Envio).filter(models.Envio.envio_id == devolucion.envio_id).first()
            if not envio:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": "not_found",
                        "message": f"Envío con ID {devolucion.envio_id} no encontrado",
                        "details": {"envio_id": devolucion.envio_id}
                    }
                )
        
        update_data = devolucion.dict(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_devolucion, field, value)
        
        db.commit()
        db.refresh(db_devolucion)
        return schemas.Devolucion(
            devolucion_id=db_devolucion.devolucion_id,
            envio_id=db_devolucion.envio_id,
            motivo=db_devolucion.motivo,
            fecha=db_devolucion.fecha,
            estado=db_devolucion.estado
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        handle_db_error(e, "actualizar devolución")

@router.delete(
    "/{devolucion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una devolución",
    description="Elimina permanentemente una devolución del sistema.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.ErrorResponse,
            "description": "No se encontró la devolución a eliminar"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al eliminar la devolución"
        }
    }
)
def delete_return(
    devolucion_id: int, 
    db: Session = Depends(get_db)
):
    """
    Elimina una devolución existente por su ID.

    Parámetros:
        devolucion_id (int): ID de la devolución a eliminar.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        None: Código de estado 204 (No Content) si la eliminación fue exitosa.

    Excepciones:
        HTTPException 404: Si no se encuentra la devolución con el ID especificado.
    """
    try:
        db_devolucion = db.query(models.Devolucion).filter(models.Devolucion.devolucion_id == devolucion_id).first()
        if not db_devolucion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "message": f"Devolución con ID {devolucion_id} no encontrada",
                    "details": {"devolucion_id": devolucion_id}
                }
            )
        
        db.delete(db_devolucion)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        handle_db_error(e, "eliminar devolución")

@router.get(
    "", 
    response_model=List[schemas.Devolucion],
    summary="Buscar devoluciones con filtros",
    description="Permite buscar devoluciones aplicando múltiples filtros opcionales.",
    response_description="Lista de devoluciones que coinciden con los criterios de búsqueda",
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
def search_returns(
    envio_id: Optional[int] = Query(
        None,
        description="ID del envío asociado a la devolución"
    ),
    motivo: Optional[str] = Query(
        None,
        min_length=2,
        max_length=500,
        description="Fragmento de texto a buscar en el motivo"
    ),
    fecha_desde: Optional[str] = Query(
        None, 
        description="Fecha mínima de devolución (formato YYYY-MM-DD)"
    ),
    fecha_hasta: Optional[str] = Query(
        None, 
        description="Fecha máxima de devolución (formato YYYY-MM-DD)"
    ),
    estado: Optional[schemas.DevolucionEstado] = Query(
        None,
        description="Estado específico de la devolución"
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
    Busca devoluciones aplicando filtros opcionales.

    Parámetros:
        envio_id (int, opcional): ID del envío asociado.
        motivo (str, opcional): Fragmento de texto en el motivo.
        fecha_desde (str, opcional): Fecha mínima de devolución.
        fecha_hasta (str, opcional): Fecha máxima de devolución.
        estado (DevolucionEstado, opcional): Estado específico.
        skip (int): Número de registros a omitir.
        limit (int): Número máximo de registros a retornar.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        List[Devolucion]: Lista de devoluciones que coinciden con los filtros aplicados.
    """
    try:
        if all(param is None for param in [envio_id, estado, motivo, fecha_desde, fecha_hasta]):
            return []

        query = db.query(models.Devolucion)
        
        if envio_id:
            query = query.filter(models.Devolucion.envio_id == envio_id)
        if motivo:
            query = query.filter(models.Devolucion.motivo.ilike(f"%{motivo}%"))
        if fecha_desde:
            query = query.filter(models.Devolucion.fecha >= f"{fecha_desde} 00:00:00")
        if fecha_hasta:
            query = query.filter(models.Devolucion.fecha <= f"{fecha_hasta} 23:59:59")
        if estado:
            query = query.filter(models.Devolucion.estado == estado)
        
        devoluciones = query.offset(skip).limit(limit).all()
        return [
            schemas.Devolucion(
                devolucion_id=d.devolucion_id,
                envio_id=d.envio_id,
                motivo=d.motivo,
                fecha=d.fecha,
                estado=d.estado
            )
            for d in devoluciones
        ]
    except Exception as e:
        handle_db_error(e, "buscar devoluciones")
        