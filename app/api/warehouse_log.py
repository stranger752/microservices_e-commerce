from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.models import models, schemas
from app.database import get_db
from typing import List, Optional
from datetime import datetime
import logging

router = APIRouter(
    prefix="/log_bodega",
    tags=["log_bodega"],
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
    response_model=List[schemas.LogBodega],
    summary="Obtener todos los registros de log de bodega",
    description="Recupera una lista paginada de todos los movimientos registrados en el log de bodega.",
    response_description="Lista de registros de log obtenida correctamente.",
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al consultar los registros de log."
        }
    }
)
def get_warehouse_logs(
    skip: int = Query(0, ge=0, description="Número de registros a omitir para paginación.", example=0),
    limit: int = Query(100, ge=1, le=1000, description="Límite máximo de registros a retornar.", example=100),
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los registros del log de bodega con paginación.

    Parámetros:
        skip (int): Número de registros a omitir.
        limit (int): Cantidad máxima de registros a retornar.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        List[LogBodega]: Lista de registros de log de bodega.
    """
    try:
        logs = db.query(models.LogBodega).offset(skip).limit(limit).all()
        return [
            schemas.LogBodega(
                log_bodega_id=l.log_bodega_id,
                producto_id=l.producto_id,
                cantidad=l.cantidad,
                fecha=l.fecha,
                bodega_id=l.bodega_id,
                empleado_id=l.empleado_id
            )
            for l in logs
        ]
    except Exception as e:
        handle_db_error(e, "obtener logs de bodega")

@router.post(
    "/", 
    response_model=schemas.LogBodega,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo registro de log de bodega",
    description="Registra un nuevo movimiento en el log de bodega con los datos proporcionados.",
    response_description="Registro de log de bodega creado exitosamente.",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": schemas.ErrorResponse,
            "description": "Datos de entrada inválidos para crear el registro."
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al crear el registro de log."
        }
    }
)
def create_warehouse_log(log: schemas.LogBodegaCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo registro en el log de bodega.

    Parámetros:
        log (LogBodegaCreate): Datos del movimiento a registrar en bodega.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        LogBodega: El registro creado con su ID generado.
    """
    try:
        db_log = models.LogBodega(**log.dict())
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        
        return schemas.LogBodega(
            log_bodega_id=db_log.log_bodega_id,
            producto_id=db_log.producto_id,
            cantidad=db_log.cantidad,
            fecha=db_log.fecha,
            bodega_id=db_log.bodega_id,
            empleado_id=db_log.empleado_id
        )
    except Exception as e:
        db.rollback()
        handle_db_error(e, "crear log de bodega")

@router.get(
    "/{log_id}", 
    response_model=schemas.LogBodega,
    summary="Obtener un registro de log por ID",
    description="Recupera los detalles de un registro específico del log de bodega mediante su ID único.",
    response_description="Registro de log encontrado exitosamente.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.ErrorResponse,
            "description": "No se encontró el registro con el ID proporcionado."
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al consultar el registro."
        }
    }
)
def get_warehouse_log(log_id: int, db: Session = Depends(get_db)):
    """
    Obtiene un registro específico del log de bodega por su ID.

    Parámetros:
        log_id (int): ID único del registro a consultar.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        LogBodega: Detalles completos del registro encontrado.
    """
    try:
        db_log = db.query(models.LogBodega).filter(models.LogBodega.log_bodega_id == log_id).first()
        if not db_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "message": f"Log de bodega con ID {log_id} no encontrado",
                    "details": {"log_id": log_id}
                }
            )

        return schemas.LogBodega(
            log_bodega_id=db_log.log_bodega_id,
            producto_id=db_log.producto_id,
            cantidad=db_log.cantidad,
            fecha=db_log.fecha,
            bodega_id=db_log.bodega_id,
            empleado_id=db_log.empleado_id
        )
    except Exception as e:
        handle_db_error(e, "obtener log de bodega")

@router.put(
    "/{log_id}", 
    response_model=schemas.LogBodega,
    summary="Actualizar un registro del log de bodega",
    description="Actualiza parcial o totalmente un registro existente en el log de bodega utilizando su ID. Solo se modificarán los campos que se incluyan en el cuerpo de la solicitud.",
    response_description="Registro actualizado exitosamente.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.ErrorResponse,
            "description": "No se encontró el registro a actualizar."
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": schemas.ErrorResponse,
            "description": "Datos de entrada inválidos."
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al actualizar el registro."
        }
    }
)
def update_warehouse_log(
    log_id: int,
    log: schemas.LogBodegaUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza parcial o totalmente un registro existente del log de bodega.

    Solo se modificarán los campos que se incluyan en el cuerpo de la solicitud.

    Parámetros:
        log_id (int): ID del registro a actualizar.
        log (LogBodegaUpdate): Campos a modificar en el registro.
        db (Session): Sesión de base de datos.

    Retorna:
        LogBodega: El registro actualizado.
    """
    try:
        db_log = db.query(models.LogBodega).filter(models.LogBodega.log_bodega_id == log_id).first()
        if not db_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "message": f"Log de bodega con ID {log_id} no encontrado",
                    "details": {"log_id": log_id}
                }
            )
        
        update_data = log.dict(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_log, field, value)
        
        db.commit()
        db.refresh(db_log)
        return schemas.LogBodega(
            log_bodega_id=db_log.log_bodega_id,
            producto_id=db_log.producto_id,
            cantidad=db_log.cantidad,
            fecha=db_log.fecha,
            bodega_id=db_log.bodega_id,
            empleado_id=db_log.empleado_id
        )
    except Exception as e:
        db.rollback()
        handle_db_error(e, "actualizar log de bodega")

@router.delete(
    "/{log_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un registro de log",
    description="Elimina permanentemente un registro específico del log de bodega.",
    response_description="Registro eliminado exitosamente.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.ErrorResponse,
            "description": "No se encontró el registro a eliminar."
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al eliminar el registro."
        }
    }
)
def delete_warehouse_log(log_id: int, db: Session = Depends(get_db)):
    """
    Elimina un registro del log de bodega por su ID.

    Parámetros:
        log_id (int): ID del registro a eliminar.
        db (Session): Sesión de base de datos.

    Retorna:
        None: Confirmación de eliminación exitosa.
    """
    try:
        db_log = db.query(models.LogBodega).filter(models.LogBodega.log_bodega_id == log_id).first()
        if not db_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "message": f"Log de bodega con ID {log_id} no encontrado",
                    "details": {"log_id": log_id}
                }
            )
        
        db.delete(db_log)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        handle_db_error(e, "eliminar log de bodega")

@router.get(
    "", 
    response_model=List[schemas.LogBodega],
    summary="Buscar registros de log con filtros",
    description="Permite buscar registros en el log de bodega aplicando múltiples filtros opcionales.",
    response_description="Lista de registros que coinciden con los criterios de búsqueda.",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": schemas.ErrorResponse,
            "description": "Parámetros de búsqueda inválidos."
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al realizar la búsqueda."
        }
    }
)
def search_warehouse_logs(
    producto_id: Optional[int] = Query(None, description="ID del producto a filtrar."),
    cantidad: Optional[int] = Query(None, description="Filtrar por cantidad exacta de productos."),
    fecha_desde: Optional[str] = Query(None, description="Fecha inicial para filtrar (formato YYYY-MM-DD)."),
    fecha_hasta: Optional[str] = Query(None, description="Fecha final para filtrar (formato YYYY-MM-DD)."),
    bodega_id: Optional[int] = Query(None, description="ID de la bodega a filtrar."),
    empleado_id: Optional[int] = Query(None, description="ID del empleado a filtrar."),
    skip: int = Query(0, ge=0, description="Número de registros a omitir.", example=0),
    limit: int = Query(100, ge=1, le=1000, description="Límite máximo de registros a retornar.", example=100),
    db: Session = Depends(get_db)
):
    """
    Busca registros en el log de bodega aplicando filtros opcionales.

    Parámetros:
        producto_id (int, opcional): ID del producto.
        cantidad (int, opcional): Cantidad exacta de productos.
        fecha_desde (str, opcional): Fecha inicial del rango (YYYY-MM-DD).
        fecha_hasta (str, opcional): Fecha final del rango (YYYY-MM-DD).
        bodega_id (int, opcional): ID de la bodega.
        empleado_id (int, opcional): ID del empleado.
        skip (int): Número de registros a omitir.
        limit (int): Límite máximo de registros.
        db (Session): Sesión de base de datos.

    Retorna:
        List[LogBodega]: Registros que coinciden con los filtros.
    """
    try:
        if all(param is None for param in [bodega_id, producto_id, empleado_id, cantidad, fecha_desde, fecha_hasta]):
            return []

        query = db.query(models.LogBodega)
        
        if producto_id:
            query = query.filter(models.LogBodega.producto_id == producto_id)
        if cantidad is not None:
            query = query.filter(models.LogBodega.cantidad == cantidad)
        if fecha_desde:
            query = query.filter(models.LogBodega.fecha >= f"{fecha_desde} 00:00:00")
        if fecha_hasta:
            query = query.filter(models.LogBodega.fecha <= f"{fecha_hasta} 23:59:59")
        if bodega_id:
            query = query.filter(models.LogBodega.bodega_id == bodega_id)
        if empleado_id:
            query = query.filter(models.LogBodega.empleado_id == empleado_id)
        
        logs = query.order_by(models.LogBodega.fecha.desc()).offset(skip).limit(limit).all()
        return [
            schemas.LogBodega(
                log_bodega_id=l.log_bodega_id,
                producto_id=l.producto_id,
                cantidad=l.cantidad,
                fecha=l.fecha,
                bodega_id=l.bodega_id,
                empleado_id=l.empleado_id
            )
            for l in logs
        ]
    except Exception as e:
        handle_db_error(e, "buscar logs de bodega")
