from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import models, schemas
from app.database import get_db
from typing import List, Optional
import logging

router = APIRouter(
    prefix="/bodega",
    tags=["bodega"],
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
    response_model=List[schemas.Bodega],
    summary="Obtener todas las bodegas",
    description="Recupera una lista paginada de todas las bodegas registradas en la base de datos.",
    response_description="Lista de bodegas obtenida correctamente.",
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse, 
            "description": "Error interno del servidor al obtener las bodegas."
        }
    }
)
def get_warehouses(
    skip: int = Query(0, ge=0, description="Número de registros a omitir desde el inicio de la consulta.", example=0),
    limit: int = Query(100, ge=1, le=1000, description="Cantidad máxima de registros a devolver.", example=50),
    db: Session = Depends(get_db)
):
    """
    Recupera una lista de todas las bodegas en la base de datos.

    Parámetros:
        skip (int): Número de registros a omitir para paginación.
        limit (int): Límite de registros a retornar.
        db (Session): Sesión activa de base de datos.

    Retorna:
        List[Bodega]: Lista de Bodegas.
    """
    try:
        bodegas = db.query(models.Bodega).offset(skip).limit(limit).all()
        return [
            schemas.Bodega(
                bodega_id=b.bodega_id,
                direccion_bodega=b.direccion_bodega,
                tipo=b.tipo
            )
            for b in bodegas
        ]
    except Exception as e:
        handle_db_error(e, "obtener bodegas")

@router.post(
    "/", 
    response_model=schemas.Bodega,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una bodega",
    description="Crea una nueva bodega con la dirección y tipo especificados.",
    response_description="Bodega creada exitosamente.",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": schemas.ErrorResponse, 
            "description": "Datos inválidos en la solicitud."
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse, "description": 
            "Error interno del servidor al crear la bodega."
        }
    }
)
def create_warehouse(
    bodega: schemas.BodegaCreate, 
    db: Session = Depends(get_db)
):
    """
    Crea una nueva bodega en la base de datos.

    Parámetros:
        bodega (BodegaCreate): Objeto que contiene la dirección y tipo de la bodega.
        db (Session): Sesión activa de base de datos (inyectada por FastAPI).

    Retorna:
        Objeto `Bodega` creado exitosamente con su ID generado.
    """
    try:
        db_bodega = models.Bodega(
            direccion_bodega=bodega.direccion_bodega,
            tipo=bodega.tipo
        )
        db.add(db_bodega)
        db.commit()
        db.refresh(db_bodega)
        return schemas.Bodega(
            bodega_id=db_bodega.bodega_id,
            direccion_bodega=db_bodega.direccion_bodega,
            tipo=db_bodega.tipo
        )
    except Exception as e:
        db.rollback()
        handle_db_error(e, "crear bodega")

@router.get(
    "/{bodega_id}", 
    response_model=schemas.Bodega,
    summary="Obtener una bodega por ID",
    description="Recupera una bodega específica mediante su ID único.",
    response_description="Bodega encontrada y retornada correctamente.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.ErrorResponse,
            "description": "No se encontró la bodega solicitada."
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse, 
            "description": "Error interno del servidor al obtener la bodega."
        }
    }
)
def get_warehouse(
    bodega_id: int, 
    db: Session = Depends(get_db)
):
    """
    Recupera los datos de una bodega específica por su ID.

    Parámetros:
    - **bodega_id** (`int`): ID único de la bodega a consultar.
    - **db** (`Session`): Sesión activa de base de datos.

    Retorna:
    - Objeto `Bodega` con los datos encontrados.
    """
    try:
        db_bodega = db.query(models.Bodega).filter(models.Bodega.bodega_id == bodega_id).first()
        if not db_bodega:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "message": f"Bodega con ID {bodega_id} no encontrada",
                    "details": {"bodega_id": bodega_id}
                }
            )
        return schemas.Bodega(
            bodega_id=db_bodega.bodega_id,
            direccion_bodega=db_bodega.direccion_bodega,
            tipo=db_bodega.tipo
        )
    except Exception as e:
        handle_db_error(e, "obtener bodega")

@router.put(
    "/{bodega_id}", 
    response_model=schemas.Bodega,
    summary="Actualizar una bodega existente",
    description="Actualiza parcial o totalmente los datos de una bodega mediante su ID. Solo se modificarán los campos proporcionados en el cuerpo de la solicitud.",
    response_description="Bodega actualizada correctamente.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.ErrorResponse,
            "description": "La bodega no existe."
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": schemas.ErrorResponse,
            "description": "Datos inválidos para actualizar."
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error al actualizar la bodega en la base de datos."
        }
    }
)
def update_warehouse(
    bodega_id: int,
    bodega: schemas.BodegaUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza parcial o totalmente los datos de una bodega existente.

    Solo se modificarán los campos que sean enviados en el cuerpo de la solicitud.

    Parámetros:
    - **bodega_id** (`int`): ID de la bodega a actualizar.
    - **bodega** (`BodegaUpdate`): Campos opcionales de la bodega a actualizar.
    - **db** (`Session`): Sesión activa de base de datos.

    Retorna:
    - Objeto `Bodega` actualizado.
    """
    try:
        db_bodega = db.query(models.Bodega).filter(models.Bodega.bodega_id == bodega_id).first()
        if not db_bodega:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "message": f"Bodega con ID {bodega_id} no encontrada",
                    "details": {"bodega_id": bodega_id}
                }
            )
        
        update_data = bodega.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_bodega, field, value)
        
        db.commit()
        db.refresh(db_bodega)

        return schemas.Bodega(
            bodega_id=db_bodega.bodega_id,
            direccion_bodega=db_bodega.direccion_bodega,
            tipo=db_bodega.tipo
        )
    except Exception as e:
        db.rollback()
        handle_db_error(e, "actualizar bodega")

@router.delete(
    "/{bodega_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una bodega",
    description="Elimina una bodega de la base de datos utilizando su ID.",
    response_description="Bodega eliminada correctamente.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": schemas.ErrorResponse,
            "description": "No se encontró la bodega a eliminar."
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse,
            "description": "Error interno al eliminar la bodega."
        }
    }
)
def delete_warehouse(
    bodega_id: int, 
    db: Session = Depends(get_db)
):
    """
    Elimina una bodega de la base de datos por su ID.

    Parámetros:
    - bodega_id (int): ID de la bodega a eliminar.
    - db (Session): Sesión activa de base de datos.

    Retorna:
    - None si la eliminación fue exitosa.
    """
    try:
        db_bodega = db.query(models.Bodega).filter(models.Bodega.bodega_id == bodega_id).first()
        if not db_bodega:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "message": f"Bodega con ID {bodega_id} no encontrada",
                    "details": {"bodega_id": bodega_id}
                }
            )
        
        db.delete(db_bodega)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        handle_db_error(e, "eliminar bodega")

@router.get(
    "", 
    response_model=List[schemas.Bodega],
    summary="Buscar bodegas usando filtros.",
    description="Filtra las bodegas por coincidencias parciales en la dirección y/o tipo especificado.",
    response_description="Listado filtrado de bodegas obtenido correctamente.",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": schemas.ErrorResponse, 
            "description": "Parámetros de búsqueda inválidos."
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": schemas.ErrorResponse, 
            "description": "Error interno al buscar bodegas."
        }
    }
)
def search_warehouses(
    direccion: Optional[str] = Query(
        None, 
        min_length=2, 
        max_length=500, 
        description="Filtrar por coincidencia parcial en la dirección."
    ),
    tipo: Optional[schemas.BodegaTipo] = Query(
        None,
        description="Filtrar por tipo de bodega ('small', 'large', 'large non-sortable'.)"
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
        le=1000,
        description="Cantidad máxima de resultados a retornar.",
        example=50
    ),
    db: Session = Depends(get_db)
):
    """
    Busca bodegas filtrando por dirección parcial y/o tipo.

    Parámetros:
        direccion (str, opcional): Texto parcial de la dirección.
        tipo (BodegaTipo, opcional): Tipo de bodega.
        skip (int): Número de registros a omitir.
        limit (int): Número máximo de registros a retornar.
        db (Session): Sesión activa de base de datos.

    Retorna:
    - Lista de objetos `Bodega` que coinciden con los filtros.
    """
    try:
        if all(param is None for param in [direccion, tipo]):
            return []

        query = db.query(models.Bodega)
        
        if tipo:
            query = query.filter(models.Bodega.tipo == tipo)
        if direccion:
            query = query.filter(models.Bodega.direccion_bodega.ilike(f"%{direccion}%"))
        
        bodegas = query.offset(skip).limit(limit).all()
        
        return [
            schemas.Bodega(
                bodega_id=b.bodega_id,
                direccion_bodega=b.direccion_bodega,
                tipo=b.tipo
            )
            for b in bodegas
        ]
    except Exception as e:
        handle_db_error(e, "buscar bodegas")
