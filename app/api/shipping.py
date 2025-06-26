from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.models import models, schemas
from app.database import get_db
from typing import List, Optional
from datetime import datetime
import random
import string
import logging

router = APIRouter(
    prefix="/envio",
    tags=["envio"],
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

def generate_tracking_code():
    """Genera un código de rastreo único compuesto por letras y dígitos aleatorios."""
    letters = string.ascii_uppercase
    digits = string.digits
    return ''.join(random.choice(letters) for _ in range(8)) + ''.join(random.choice(digits) for _ in range(12))

@router.get(
    "/", 
    response_model=List[schemas.Envio],
    summary="Obtener todos los envíos",
    description="Obtiene una lista paginada de todos los envíos registrados en el sistema.",
    response_description="Lista de envíos obtenida correctamente",
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al obtener la lista de envíos"
        }
    }
)
def get_shippings(
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
    Recupera una lista paginada de todos los envíos registrados.

    Parámetros:
        skip (int): Número de registros a omitir.
        limit (int): Límite de registros a retornar.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        List[Envio]: Lista de objetos Envio con sus datos básicos.
    """
    try:
        envios = db.query(models.Envio).offset(skip).limit(limit).all()
        return [
            schemas.Envio(
                envio_id=e.envio_id,
                pedido_id=e.pedido_id,
                direccion_id=e.direccion_id,
                metodo_envio_id=e.metodo_envio_id,
                fecha_envio=e.fecha_envio,
                fecha_estimada_entrega=e.fecha_estimada_entrega,
                codigo_rastreo=e.codigo_rastreo
            )
            for e in envios
        ]
    except Exception as e:
        handle_db_error(e, "obtener envíos")

@router.post(
    "/", 
    response_model=schemas.Envio,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo envío",
    description="Registra un nuevo envío en el sistema con un código de rastreo único y estado inicial.",
    response_description="Detalles del envío creado",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": schemas.ErrorResponse,
            "description": "Datos de envío inválidos o incompletos"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al crear el envío"
        }
    }
)
def create_shipping(
    envio: schemas.EnvioCreate, 
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo registro de envío con estado inicial 'pendiente'.

    Parámetros:
        envio (EnvioCreate): Datos del envío a crear.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        Envio: Objeto con los datos del envío creado, incluyendo código de rastreo.
    """
    try:
        tracking_code = generate_tracking_code()
        while db.query(models.Envio).filter(models.Envio.codigo_rastreo == tracking_code).first():
            tracking_code = generate_tracking_code()
        
        db_envio = models.Envio(**envio.dict(), codigo_rastreo=tracking_code)
        db.add(db_envio)
        db.commit()
        db.refresh(db_envio)
        
        db_estado = models.EstadoEnvio(
            envio_id=db_envio.envio_id,
            estado="pendiente",
            descripcion="Envío creado, pendiente de procesamiento"
        )
        db.add(db_estado)
        db.commit()
        
        return schemas.Envio(
            envio_id=db_envio.envio_id,
            pedido_id=db_envio.pedido_id,
            direccion_id=db_envio.direccion_id,
            metodo_envio_id=db_envio.metodo_envio_id,
            fecha_envio=db_envio.fecha_envio,
            fecha_estimada_entrega=db_envio.fecha_estimada_entrega,
            codigo_rastreo=db_envio.codigo_rastreo
        )
    except Exception as e:
        db.rollback()
        handle_db_error(e, "crear envío")

@router.get(
    "/{envio_id}", 
    response_model=schemas.Envio,
    summary="Obtener un envío por ID",
    description="Recupera los detalles completos de un envío específico usando su ID único.",
    response_description="Detalles del envío encontrado",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.ErrorResponse,
            "description": "No se encontró un envío con el ID especificado"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al obtener el envío"
        }
    }
)
def get_shipping(
    envio_id: int, 
    db: Session = Depends(get_db)
):
    """
    Obtiene los detalles de un envío específico por su ID.

    Parámetros:
        envio_id (int): ID único del envío a consultar.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        Envio: Objeto con todos los datos del envío solicitado.

    Excepciones:
        HTTPException 404: Si no se encuentra el envío con el ID especificado.
    """
    try:
        db_envio = db.query(models.Envio).filter(models.Envio.envio_id == envio_id).first()
        if not db_envio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "message": f"Envío con ID {envio_id} no encontrado",
                    "details": {"envio_id": envio_id}
                }
            )

        return schemas.Envio(
            envio_id=db_envio.envio_id,
            pedido_id=db_envio.pedido_id,
            direccion_id=db_envio.direccion_id,
            metodo_envio_id=db_envio.metodo_envio_id,
            fecha_envio=db_envio.fecha_envio,
            fecha_estimada_entrega=db_envio.fecha_estimada_entrega,
            codigo_rastreo=db_envio.codigo_rastreo
        )
    except Exception as e:
        handle_db_error(e, "obtener envío")

@router.put(
    "/{envio_id}", 
    response_model=schemas.Envio,
    summary="Actualizar un envío",
    description="Actualiza parcial o totalmente los datos de un envío existente utilizando su ID. Solo se modificarán los campos enviados en el cuerpo de la solicitud.",
    response_description="Detalles del envío actualizado",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.ErrorResponse,
            "description": "No se encontró el envío a actualizar"
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": schemas.ErrorResponse,
            "description": "Datos de envío inválidos"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al actualizar el envío"
        }
    }
)
def update_shipping(
    envio_id: int,
    envio: schemas.EnvioUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza parcial o totalmente un envío existente.

    Solo se modificarán los campos que sean enviados en el cuerpo de la solicitud.

    Parámetros:
        envio_id (int): ID del envío a actualizar.
        envio (EnvioUpdate): Datos del envío a modificar. Solo los campos presentes serán actualizados.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        Envio: Objeto con los datos actualizados del envío.

    Excepciones:
        HTTPException 404: Si no se encuentra el envío con el ID especificado.
        HTTPException 400: Si los datos enviados no son válidos.
        HTTPException 500: Si ocurre un error interno en la base de datos.
    """
    try:
        db_envio = db.query(models.Envio).filter(models.Envio.envio_id == envio_id).first()
        if not db_envio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "message": f"Envío con ID {envio_id} no encontrado",
                    "details": {"envio_id": envio_id}
                }
            )
        
        update_data = envio.dict(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_envio, field, value)
        
        db.commit()
        db.refresh(db_envio)
        return schemas.Envio(
            envio_id=db_envio.envio_id,
            pedido_id=db_envio.pedido_id,
            direccion_id=db_envio.direccion_id,
            metodo_envio_id=db_envio.metodo_envio_id,
            fecha_envio=db_envio.fecha_envio,
            fecha_estimada_entrega=db_envio.fecha_estimada_entrega,
            codigo_rastreo=db_envio.codigo_rastreo
        )
    except Exception as e:
        db.rollback()
        handle_db_error(e, "actualizar envío")

@router.delete(
    "/{envio_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un envío",
    description="Elimina permanentemente un envío del sistema.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.ErrorResponse,
            "description": "No se encontró el envío a eliminar"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al eliminar el envío"
        }
    }
)
def delete_shipping(
    envio_id: int, 
    db: Session = Depends(get_db)
):
    """
    Elimina un envío existente por su ID.

    Parámetros:
        envio_id (int): ID del envío a eliminar.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        None: Código de estado 204 (No Content) si la eliminación fue exitosa.

    Excepciones:
        HTTPException 404: Si no se encuentra el envío con el ID especificado.
    """
    try:
        db_envio = db.query(models.Envio).filter(models.Envio.envio_id == envio_id).first()
        if not db_envio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "message": f"Envío con ID {envio_id} no encontrado",
                    "details": {"envio_id": envio_id}
                }
            )
        
        db.delete(db_envio)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        handle_db_error(e, "eliminar envío")

@router.get(
    "", 
    response_model=List[schemas.Envio],
    summary="Buscar envíos usando filtros.",
    description="Permite buscar envíos aplicando filtros por rangos de fechas.",
    response_description="Lista de envíos que coinciden con los criterios de búsqueda",
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
def search_shippings_range(
    pedido_id: Optional[int] = Query(
        None,
        description="ID del pedido asociado al envío"
    ),
    direccion_id: Optional[int] = Query(
        None,
        description="ID de la dirección de envío"
    ),
    metodo_envio_id: Optional[int] = Query(
        None,
        description="ID del método de envío utilizado"
    ),
    fecha_envio_desde: Optional[str] = Query(
        None, 
        description="Fecha mínima de envío (formato YYYY-MM-DD)"
    ),
    fecha_envio_hasta: Optional[str] = Query(
        None, 
        description="Fecha máxima de envío (formato YYYY-MM-DD)"
    ),
    fecha_estimada_desde: Optional[str] = Query(
        None, 
        description="Fecha mínima estimada de entrega (formato YYYY-MM-DD)"
    ),
    fecha_estimada_hasta: Optional[str] = Query(
        None, 
        description="Fecha máxima estimada de entrega (formato YYYY-MM-DD)"
    ),
    codigo_rastreo: Optional[str] = Query(
        None, 
        min_length=8, 
        max_length=20,
        description="Fragmento del código de rastreo (búsqueda parcial)"
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
    Busca envíos aplicando filtros por rangos de fechas y otros atributos.

    Parámetros:
        pedido_id (int, opcional): ID del pedido asociado.
        direccion_id (int, opcional): ID de la dirección.
        metodo_envio_id (int, opcional): ID del método de envío.
        fecha_envio_desde (str, opcional): Fecha mínima de envío.
        fecha_envio_hasta (str, opcional): Fecha máxima de envío.
        fecha_estimada_desde (str, opcional): Fecha mínima estimada de entrega.
        fecha_estimada_hasta (str, opcional): Fecha máxima estimada de entrega.
        codigo_rastreo (str, opcional): Fragmento del código de rastreo.
        skip (int): Número de registros a omitir.
        limit (int): Número máximo de registros a retornar.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        List[Envio]: Lista de envíos que coinciden con los filtros aplicados.
    """
    try:
        if all(param is None for param in [
            pedido_id, direccion_id, metodo_envio_id, codigo_rastreo,
            fecha_envio_desde, fecha_envio_hasta,
            fecha_estimada_desde, fecha_estimada_hasta
        ]):
            return []

        query = db.query(models.Envio)
        
        if pedido_id:
            query = query.filter(models.Envio.pedido_id == pedido_id)
        if direccion_id:
            query = query.filter(models.Envio.direccion_id == direccion_id)
        if metodo_envio_id:
            query = query.filter(models.Envio.metodo_envio_id == metodo_envio_id)
        if fecha_envio_desde:
            query = query.filter(models.Envio.fecha_envio >= f"{fecha_envio_desde} 00:00:00")
        if fecha_envio_hasta:
            query = query.filter(models.Envio.fecha_envio <= f"{fecha_envio_hasta} 23:59:59")
        if fecha_estimada_desde:
            query = query.filter(models.Envio.fecha_estimada_entrega >= f"{fecha_estimada_desde} 00:00:00")
        if fecha_estimada_hasta:
            query = query.filter(models.Envio.fecha_estimada_entrega <= f"{fecha_estimada_hasta} 23:59:59")
        if codigo_rastreo:
            query = query.filter(models.Envio.codigo_rastreo.ilike(f"%{codigo_rastreo}%"))
        
        envios = query.offset(skip).limit(limit).all()
        return [
            schemas.Envio(
                envio_id=e.envio_id,
                pedido_id=e.pedido_id,
                direccion_id=e.direccion_id,
                metodo_envio_id=e.metodo_envio_id,
                fecha_envio=e.fecha_envio,
                fecha_estimada_entrega=e.fecha_estimada_entrega,
                codigo_rastreo=e.codigo_rastreo
            )
            for e in envios
        ]
    except Exception as e:
        handle_db_error(e, "buscar envíos por rango")

@router.get(
    "/track/{tracking_code}", 
    response_model=List[schemas.EstadoEnvio],
    summary="Rastrear un envío",
    description="Obtiene el historial completo de estados de un envío específico usando su código de rastreo.",
    response_description="Historial de estados del envío",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.ErrorResponse,
            "description": "No se encontró un envío con el código de rastreo especificado"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al rastrear el envío"
        }
    }
)
def track_shipping(
    tracking_code: str, 
    db: Session = Depends(get_db)
):
    """
    Recupera el historial completo de estados de un envío por su código de rastreo.

    Parámetros:
        tracking_code (str): Código de rastreo único del envío.
        db (Session): Sesión de base de datos inyectada.

    Retorna:
        List[EstadoEnvio]: Lista ordenada de estados por los que ha pasado el envío.

    Excepciones:
        HTTPException 404: Si no se encuentra el envío con el código especificado.
    """
    try:
        envio = db.query(models.Envio).filter(models.Envio.codigo_rastreo == tracking_code).first()
        if not envio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "message": f"Código de rastreo {tracking_code} no encontrado",
                    "details": {"tracking_code": tracking_code}
                }
            )
        
        estados = db.query(models.EstadoEnvio)\
            .filter(models.EstadoEnvio.envio_id == envio.envio_id)\
            .order_by(models.EstadoEnvio.fecha.desc())\
            .all()
        
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
        handle_db_error(e, "rastrear envío")