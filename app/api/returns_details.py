from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.models import models, schemas
from app.database import get_db
from typing import List, Optional
import logging

router = APIRouter(
    prefix="/devolucion_detalle",
    tags=["devolucion_detalle"],
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
    response_model=List[schemas.DevolucionDetalle],
    summary="Obtener todos los detalles de devolución",
    description="Obtiene una lista paginada de todos los detalles de devolución registrados en el sistema.",
    response_description="Lista de detalles de devolución obtenida correctamente",
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al obtener la lista de detalles"
        }
    }
)
def get_return_details(
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
    Recupera una lista paginada de todos los detalles de devolución registrados.

    Parámetros:
        skip (int): Número de registros a omitir.
        limit (int): Límite de registros a retornar.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        List[DevolucionDetalle]: Lista de objetos DevolucionDetalle con sus datos básicos.
    """
    try:
        detalles = db.query(models.DevolucionDetalle).offset(skip).limit(limit).all()
        return [
            schemas.DevolucionDetalle(
                devolucion_detalle_id=d.devolucion_detalle_id,
                devolucion_id=d.devolucion_id,
                producto_id=d.producto_id,
                cantidad=d.cantidad
            )
            for d in detalles
        ]
    except Exception as e:
        handle_db_error(e, "obtener detalles de devolución")

@router.post(
    "/", 
    response_model=schemas.DevolucionDetalle,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo detalle de devolución",
    description="Registra un nuevo detalle de devolución asociado a una devolución existente.",
    response_description="Detalles del detalle de devolución creado",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": schemas.ErrorResponse,
            "description": "Datos de entrada inválidos o incompletos"
        },
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.ErrorResponse,
            "description": "No se encontró la devolución asociada"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al crear el detalle de devolución"
        }
    }
)
def create_return_detail(
    detalle: schemas.DevolucionDetalleCreate, 
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo registro de detalle de devolución.

    Parámetros:
        detalle (DevolucionDetalleCreate): Objeto con los datos del detalle a crear.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        DevolucionDetalle: Objeto con los datos del detalle creado, incluyendo su ID generado.

    Excepciones:
        HTTPException 404: Si no se encuentra la devolución asociada.
    """
    try:
        devolucion = db.query(models.Devolucion).filter(
            models.Devolucion.devolucion_id == detalle.devolucion_id
        ).first()
        
        if not devolucion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "message": f"Devolución con ID {detalle.devolucion_id} no encontrada",
                    "details": {"devolucion_id": detalle.devolucion_id}
                }
            )
        
        db_detalle = models.DevolucionDetalle(**detalle.dict())
        db.add(db_detalle)
        db.commit()
        db.refresh(db_detalle)
        
        return schemas.DevolucionDetalle(
            devolucion_detalle_id=db_detalle.devolucion_detalle_id,
            devolucion_id=db_detalle.devolucion_id,
            producto_id=db_detalle.producto_id,
            cantidad=db_detalle.cantidad
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        handle_db_error(e, "crear detalle de devolución")

@router.get(
    "/{detalle_id}", 
    response_model=schemas.DevolucionDetalle,
    summary="Obtener un detalle de devolución por ID",
    description="Recupera los detalles completos de un detalle de devolución específico usando su ID único.",
    response_description="Detalles del detalle de devolución encontrado",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.ErrorResponse,
            "description": "No se encontró un detalle con el ID especificado"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al obtener el detalle de devolución"
        }
    }
)
def get_return_detail(
    detalle_id: int, 
    db: Session = Depends(get_db)
):
    """
    Obtiene los detalles de un detalle de devolución específico por su ID.

    Parámetros:
        detalle_id (int): ID único del detalle a consultar.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        DevolucionDetalle: Objeto con todos los datos del detalle solicitado.

    Excepciones:
        HTTPException 404: Si no se encuentra el detalle con el ID especificado.
    """
    try:
        db_detalle = db.query(models.DevolucionDetalle).filter(
            models.DevolucionDetalle.devolucion_detalle_id == detalle_id
        ).first()
        
        if not db_detalle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "message": f"Detalle de devolución con ID {detalle_id} no encontrado",
                    "details": {"detalle_id": detalle_id}
                }
            )

        return schemas.DevolucionDetalle(
            devolucion_detalle_id=db_detalle.devolucion_detalle_id,
            devolucion_id=db_detalle.devolucion_id,
            producto_id=db_detalle.producto_id,
            cantidad=db_detalle.cantidad
        )
    except Exception as e:
        handle_db_error(e, "obtener detalle de devolución")

@router.put(
    "/{detalle_id}", 
    response_model=schemas.DevolucionDetalle,
    summary="Actualizar un detalle de devolución",
    description="Actualiza uno o más campos de un detalle de devolución existente utilizando su ID. No es necesario enviar todos los campos.",
    response_description="Detalle de devolución actualizado correctamente.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.ErrorResponse,
            "description": "No se encontró el detalle o la devolución asociada"
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": schemas.ErrorResponse,
            "description": "Datos de detalle inválidos"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al actualizar el detalle de devolución"
        }
    }
)
def update_return_detail(
    detalle_id: int,
    detalle: schemas.DevolucionDetalleUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza parcial o totalmente un detalle de devolución existente.

    Solo se modificarán los campos que sean enviados en el cuerpo de la solicitud.

    Parámetros:
        detalle_id (int): ID del detalle de devolución a modificar.
        detalle (DevolucionDetalleUpdate): Datos opcionales del detalle de devolución a actualizar.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        DevolucionDetalle: Representación del detalle de devolución actualizado.
    """
    try:
        db_detalle = db.query(models.DevolucionDetalle).filter(
            models.DevolucionDetalle.devolucion_detalle_id == detalle_id
        ).first()
        
        if not db_detalle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "message": f"Detalle de devolución con ID {detalle_id} no encontrado",
                    "details": {"detalle_id": detalle_id}
                }
            )

        if detalle.devolucion_id is not None:
            devolucion = db.query(models.Devolucion).filter(
                models.Devolucion.devolucion_id == detalle.devolucion_id
            ).first()
            
            if not devolucion:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": "not_found",
                        "message": f"Devolución con ID {detalle.devolucion_id} no encontrada",
                        "details": {"devolucion_id": detalle.devolucion_id}
                    }
                )

        update_data = detalle.dict(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_detalle, field, value)
        
        db.commit()
        db.refresh(db_detalle)
        
        return schemas.DevolucionDetalle(
            devolucion_detalle_id=db_detalle.devolucion_detalle_id,
            devolucion_id=db_detalle.devolucion_id,
            producto_id=db_detalle.producto_id,
            cantidad=db_detalle.cantidad
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        handle_db_error(e, "actualizar detalle de devolución")

@router.delete(
    "/{detalle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un detalle de devolución",
    description="Elimina permanentemente un detalle de devolución del sistema.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.ErrorResponse,
            "description": "No se encontró el detalle a eliminar"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al eliminar el detalle de devolución"
        }
    }
)
def delete_return_detail(
    detalle_id: int, 
    db: Session = Depends(get_db)
):
    """
    Elimina un detalle de devolución existente por su ID.

    Parámetros:
        detalle_id (int): ID del detalle a eliminar.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        None: Código de estado 204 (No Content) si la eliminación fue exitosa.

    Excepciones:
        HTTPException 404: Si no se encuentra el detalle con el ID especificado.
    """
    try:
        db_detalle = db.query(models.DevolucionDetalle).filter(
            models.DevolucionDetalle.devolucion_detalle_id == detalle_id
        ).first()
        
        if not db_detalle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "message": f"Detalle de devolución con ID {detalle_id} no encontrado",
                    "details": {"detalle_id": detalle_id}
                }
            )
        
        db.delete(db_detalle)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        handle_db_error(e, "eliminar detalle de devolución")

@router.get(
    "", 
    response_model=List[schemas.DevolucionDetalle],
    summary="Buscar detalles de devolución con filtros",
    description="Permite buscar detalles de devolución aplicando múltiples filtros opcionales.",
    response_description="Lista de detalles de devolución que coinciden con los criterios de búsqueda",
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
def search_return_details(
    devolucion_id: Optional[int] = Query(
        None,
        description="ID de la devolución asociada al detalle"
    ),
    producto_id: Optional[int] = Query(
        None,
        description="ID del producto asociado al detalle"
    ),
    cantidad: Optional[int] = Query(
        None, 
        ge=0,
        description="Cantidad exacta de productos devueltos"
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
    Busca detalles de devolución aplicando filtros opcionales.

    Parámetros:
        devolucion_id (int, opcional): ID de la devolución asociada.
        producto_id (int, opcional): ID del producto asociado.
        cantidad (int, opcional): Cantidad exacta de productos devueltos.
        skip (int): Número de registros a omitir.
        limit (int): Número máximo de registros a retornar.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        List[DevolucionDetalle]: Lista de detalles que coinciden con los filtros aplicados.
    """
    try:
        if all(param is None for param in [devolucion_id, producto_id, cantidad]):
            return []

        query = db.query(models.DevolucionDetalle)
        
        if devolucion_id:
            query = query.filter(models.DevolucionDetalle.devolucion_id == devolucion_id)
        if producto_id:
            query = query.filter(models.DevolucionDetalle.producto_id == producto_id)
        if cantidad:
            query = query.filter(models.DevolucionDetalle.cantidad == cantidad)
        
        detalles = query.offset(skip).limit(limit).all()
        return [
            schemas.DevolucionDetalle(
                devolucion_detalle_id=d.devolucion_detalle_id,
                devolucion_id=d.devolucion_id,
                producto_id=d.producto_id,
                cantidad=d.cantidad
            )
            for d in detalles
        ]
    except Exception as e:
        handle_db_error(e, "buscar detalles de devolución")
