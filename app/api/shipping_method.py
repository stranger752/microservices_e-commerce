from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import models, schemas
from app.database import get_db
from typing import List, Optional
import logging

router = APIRouter(
    prefix="/metodo_envio",
    tags=["metodo_envio"],
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
    response_model=List[schemas.MetodoEnvio],
    summary="Obtener todos los métodos de envío",
    description="Recupera una lista paginada de todos los métodos de envío registrados en la base de datos.",
    response_description="Lista de métodos de envío recuperados correctamente.",
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al consultar los métodos de envío."
        }
    }
)
def get_shipping_methods(
    skip: int = Query(0, ge=0, description="Número de registros a omitir desde el inicio de la consulta.", example=0),
    limit: int = Query(100, ge=1, le=1000, description="Cantidad máxima de registros a devolver.", example=50),
    db: Session = Depends(get_db)
):
    """
    Recupera una lista de métodos de envío desde la base de datos.

    Parámetros:
        skip (int): Número de registros a omitir para paginación.
        limit (int): Límite de registros a retornar.
        db (Session): Sesión de base de datos.

    Retorna:
        List[MetodoEnvio]: Lista de métodos de envío disponibles.
    """
    try:
        metodos = db.query(models.MetodoEnvio).offset(skip).limit(limit).all()
        return [
            schemas.MetodoEnvio(
                metodo_envio_id=m.metodo_envio_id,
                tipo=m.tipo,
                descripcion=m.descripcion,
                tiempo_estimado=m.tiempo_estimado,
                costo=float(m.costo)
            )
            for m in metodos
        ]
    except Exception as e:
        handle_db_error(e, "obtener métodos de envío")

@router.post(
    "/",
    response_model=schemas.MetodoEnvio,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo método de envío",
    description="Registra un nuevo método de envío en la base de datos.",
    response_description="Método de envío creado correctamente.",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": schemas.ErrorResponse,
            "description": "Datos de entrada inválidos para crear el método de envío."
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al crear el método de envío."
        }
    }
)
def create_shipping_method(
    metodo_envio: schemas.MetodoEnvioCreate,
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo método de envío en la base de datos.

    Parámetros:
        metodo_envio (MetodoEnvioCreate): Datos del nuevo método de envío.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        MetodoEnvio: El método de envío creado con su ID generado.
    """
    try:
        db_metodo_envio = models.MetodoEnvio(
            tipo=metodo_envio.tipo,
            descripcion=metodo_envio.descripcion,
            tiempo_estimado=metodo_envio.tiempo_estimado,
            costo=metodo_envio.costo
        )
        db.add(db_metodo_envio)
        db.commit()
        db.refresh(db_metodo_envio)
        return schemas.MetodoEnvio(
            metodo_envio_id=db_metodo_envio.metodo_envio_id,
            tipo=db_metodo_envio.tipo,
            descripcion=db_metodo_envio.descripcion,
            tiempo_estimado=db_metodo_envio.tiempo_estimado,
            costo=float(db_metodo_envio.costo)
        )
    except Exception as e:
        db.rollback()
        handle_db_error(e, "crear método de envío")

@router.get(
    "/{metodo_envio_id}",
    response_model=schemas.MetodoEnvio,
    summary="Obtener un método de envío por ID",
    description="Devuelve los detalles de un método de envío específico dado su ID.",
    response_description="Método de envío encontrado correctamente.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.ErrorResponse,
            "description": "No se encontró un método de envío con el ID proporcionado."
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al consultar el método de envío."
        }
    }
)
def get_shipping_method(
    metodo_envio_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene los detalles de un método de envío específico.

    Parámetros:
        metodo_envio_id (int): ID del método de envío.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        MetodoEnvio: Detalles del método de envío correspondiente.
    """
    try:
        db_metodo = db.query(models.MetodoEnvio).filter(models.MetodoEnvio.metodo_envio_id == metodo_envio_id).first()
        if not db_metodo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "message": f"Método de envío con ID {metodo_envio_id} no encontrado",
                    "details": {"metodo_envio_id": metodo_envio_id}
                }
            )
        return schemas.MetodoEnvio(
            metodo_envio_id=db_metodo.metodo_envio_id,
            tipo=db_metodo.tipo,
            descripcion=db_metodo.descripcion,
            tiempo_estimado=db_metodo.tiempo_estimado,
            costo=float(db_metodo.costo)
        )
    except Exception as e:
        handle_db_error(e, "obtener método de envío")

@router.put(
    "/{metodo_envio_id}",
    response_model=schemas.MetodoEnvio,
    summary="Actualizar un método de envío",
    description="Actualiza uno o más campos de un método de envío existente utilizando su ID. No es necesario enviar todos los campos.",
    response_description="Método de envío actualizado correctamente.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.ErrorResponse,
            "description": "No se encontró el método de envío a actualizar."
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": schemas.ErrorResponse,
            "description": "Datos de entrada inválidos."
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al actualizar el método de envío."
        }
    }
)
def update_shipping_method(
    metodo_envio_id: int,
    metodo_envio: schemas.MetodoEnvioUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza parcial o totalmente un método de envío existente.

    Solo se modificarán los campos que sean enviados en el cuerpo de la solicitud.

    Parámetros:
        metodo_envio_id (int): ID del método de envío a modificar.
        metodo_envio (MetodoEnvioUpdate): Datos opcionales del método de envío a actualizar.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        MetodoEnvio: Representación del método de envío actualizado.
    """
    try:
        db_metodo = db.query(models.MetodoEnvio).filter(models.MetodoEnvio.metodo_envio_id == metodo_envio_id).first()
        if not db_metodo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "message": f"Método de envío con ID {metodo_envio_id} no encontrado",
                    "details": {"metodo_envio_id": metodo_envio_id}
                }
            )

        update_data = metodo_envio.dict(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_metodo, field, value)

        db.commit()
        db.refresh(db_metodo)

        return schemas.MetodoEnvio(
            metodo_envio_id=db_metodo.metodo_envio_id,
            tipo=db_metodo.tipo,
            descripcion=db_metodo.descripcion,
            tiempo_estimado=db_metodo.tiempo_estimado,
            costo=float(db_metodo.costo)
        )

    except Exception as e:
        db.rollback()
        handle_db_error(e, "actualizar parcialmente método de envío")

@router.delete(
    "/{metodo_envio_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un método de envío",
    description="Elimina un método de envío de la base de datos dado su ID.",
    response_description="Método de envío eliminado exitosamente.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.ErrorResponse,
            "description": "No se encontró el método de envío a eliminar."
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al eliminar el método de envío."
        }
    }
)
def delete_shipping_method(
    metodo_envio_id: int,
    db: Session = Depends(get_db)
):
    """
    Elimina un método de envío existente por su ID.

    Parámetros:
        metodo_envio_id (int): ID del método de envío a eliminar.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        None
    """
    try:
        db_metodo = db.query(models.MetodoEnvio).filter(models.MetodoEnvio.metodo_envio_id == metodo_envio_id).first()
        if not db_metodo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "message": f"Método de envío con ID {metodo_envio_id} no encontrado",
                    "details": {"metodo_envio_id": metodo_envio_id}
                }
            )
        db.delete(db_metodo)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        handle_db_error(e, "eliminar método de envío")

@router.get(
    "",
    response_model=List[schemas.MetodoEnvio],
    summary="Buscar métodos de envío usando filtros",
    description=(
        "Permite buscar métodos de envío aplicando filtros opcionales como tipo, "
        "descripción, rango de tiempo estimado y rango de costo."
    ),
    response_description="Lista de métodos de envío que coinciden con los filtros.",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": schemas.ErrorResponse,
            "description": "Parámetros de búsqueda inválidos."
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno durante la búsqueda."
        }
    }
)
def search_shipping_methods(
    tipo: Optional[schemas.MetodoEnvioTipo] = Query(
        None,
        description="Filtrar por tipo de envío ('estandar', 'rapido', 'express')."
    ),
    descripcion: Optional[str] = Query(
        None,
        min_length=2,
        max_length=100,
        description="Filtrar por coincidencia parcial en la descripción del método."
    ),
    tiempo_estimado_min: Optional[int] = Query(
        None,
        ge=1,
        description="Filtrar por tiempo estimado mínimo de entrega (en días)."
    ),
    tiempo_estimado_max: Optional[int] = Query(
        None,
        ge=1,
        description="Filtrar por tiempo estimado máximo de entrega (en días)."
    ),
    costo_min: Optional[float] = Query(
        None,
        ge=0,
        description="Filtrar por costo mínimo del envío."
    ),
    costo_max: Optional[float] = Query(
        None,
        ge=0,
        description="Filtrar por costo máximo del envío."
    ),
    skip: int = Query(
        0,
        ge=0,
        description="Número de resultados a omitir (paginación).",
        example=0
    ),
    limit: int = Query(
        100,
        ge=1,
        le=500,
        description="Cantidad máxima de resultados a retornar.",
        example=50
    ),
    db: Session = Depends(get_db)
):
    """
    Realiza una búsqueda avanzada de métodos de envío aplicando filtros opcionales.

    Parámetros:
        tipo (MetodoEnvioTipo, opcional): Tipo de envío a filtrar.
        descripcion (str, opcional): Texto parcial para buscar en la descripción.
        tiempo_estimado_min (int, opcional): Tiempo mínimo de entrega en días.
        tiempo_estimado_max (int, opcional): Tiempo máximo de entrega en días.
        costo_min (float, opcional): Costo mínimo del método de envío.
        costo_max (float, opcional): Costo máximo del método de envío.
        skip (int): Desplazamiento para paginación.
        limit (int): Límite de resultados a retornar.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        List[MetodoEnvio]: Lista de métodos de envío que cumplen los filtros especificados.
    """
    try:
        if all(param is None for param in [tipo, descripcion, tiempo_estimado_min, tiempo_estimado_max, costo_min, costo_max]):
            return []

        query = db.query(models.MetodoEnvio)

        if tipo:
            query = query.filter(models.MetodoEnvio.tipo == tipo)
        if descripcion:
            query = query.filter(models.MetodoEnvio.descripcion.ilike(f"%{descripcion}%"))
        if tiempo_estimado_min is not None:
            query = query.filter(models.MetodoEnvio.tiempo_estimado >= tiempo_estimado_min)
        if tiempo_estimado_max is not None:
            query = query.filter(models.MetodoEnvio.tiempo_estimado <= tiempo_estimado_max)
        if costo_min is not None:
            query = query.filter(models.MetodoEnvio.costo >= costo_min)
        if costo_max is not None:
            query = query.filter(models.MetodoEnvio.costo <= costo_max)

        metodos = query.offset(skip).limit(limit).all()

        return [
            schemas.MetodoEnvio(
                metodo_envio_id=m.metodo_envio_id,
                tipo=m.tipo,
                descripcion=m.descripcion,
                tiempo_estimado=m.tiempo_estimado,
                costo=float(m.costo)
            )
            for m in metodos
        ]
    except Exception as e:
        handle_db_error(e, "buscar métodos de envío")
