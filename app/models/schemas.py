from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

# -----------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    """
    Esquema para la respuesta de error estándar en la API.

    Attributes:
        error (str): Código del tipo de error ocurrido.
        message (str): Mensaje descriptivo del error.
        details (Optional[dict]): Información adicional sobre el error.
    """
    error: str = Field(
        ..., 
        example="not_found", 
        description="Código identificador del error."
    )
    message: str = Field(
        ..., 
        example="Recurso no encontrado", 
        description="Mensaje descriptivo del error."
    )
    details: Optional[dict] = Field(
        None, 
        description="Detalles adicionales del error, claves específicas."
    )

# -----------------------------------------------------------------------------

class MetodoEnvioTipo(str, Enum):
    """
    Enumeración de tipos válidos para el método de envío.
    """
    estandar = "estandar"
    rapido = "rapido"
    express = "express"

class MetodoEnvioBase(BaseModel):
    """
    Esquema base para un método de envío con campos comunes.
    """
    tipo: MetodoEnvioTipo = Field(
        ...,
        description="Tipo de método de envío: 'estandar', 'rapido', 'express'",
        example="express"
    )
    descripcion: str = Field(
        ..., 
        min_length=2,
        max_length=250,
        description="Descripción detallada del método de envío.",
        example="Envío express con entrega en 24 horas."
    )
    tiempo_estimado: int = Field(
        ...,
        gt=0,
        description="Tiempo estimado de entrega en días (entero positivo).",
        example=1
    )
    costo: float = Field(
        ...,
        ge=0,
        description="Costo del método de envío (número positivo o cero).",
        example=100.00
    )

class MetodoEnvioCreate(MetodoEnvioBase):
    """
    Esquema para la creación de un método de envío.
    Utiliza los mismos campos que MetodoEnvioBase.
    """
    pass

class MetodoEnvio(MetodoEnvioBase):
    """
    Esquema para representar un método de envío completo incluyendo su ID.
    """
    metodo_envio_id: int = Field(
        ...,
        description="ID único del método de envío generado automáticamente."
    )

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class MetodoEnvioUpdate(BaseModel):
    """
    Esquema para la actualización parcial de un método de envío.
    """
    tipo: Optional[MetodoEnvioTipo] = Field(
        None,
        description="Tipo de método de envío: 'estandar', 'rapido', 'express'",
        example="express"
    )
    descripcion: Optional[str] = Field(
        None,
        min_length=2,
        max_length=250,
        description="Descripción detallada del método de envío.",
        example="Envío express con entrega en 24 horas."
    )
    tiempo_estimado: Optional[int] = Field(
        None,
        gt=0,
        description="Tiempo estimado de entrega en días (entero positivo).",
        example=1
    )
    costo: Optional[float] = Field(
        None,
        ge=0,
        description="Costo del método de envío (número positivo o cero).",
        example=100.00
    )

# -----------------------------------------------------------------------------

class BodegaTipo(str, Enum):
    """
    Enumeración de tipos de bodegas permitidos.
    """
    small = "small"
    large = "large"
    non_sortable = "large non-sortable"

class BodegaBase(BaseModel):
    """
    Esquema base para una bodega con campos comunes.
    """
    direccion_bodega: str = Field(
        ...,
        min_length=2,
        max_length=500,
        description="Dirección de la bodega",
        example="Av. Independencia No. 123, Col. Universidad, Toluca, México."
    )
    tipo: BodegaTipo = Field(
        ...,
        description="Tipo de bodega: 'small', 'large', 'large non-sortable'",
        example="large"
    )

class BodegaCreate(BodegaBase):
    """
    Esquema para la creación de una bodega.
    Utiliza los mismos campos que BodegaBase.
    """
    pass

class Bodega(BodegaBase):
    """
    Esquema para representar una bodega completa incluyendo su ID.
    """
    bodega_id: int = Field(
        ...,
        description="ID único de la bodega generado automáticamente."
    )

    class Config:
        from_attributes = True

class BodegaUpdate(BaseModel):
    """
    Esquema para la actualización parcial de una bodega.
    """
    direccion_bodega: Optional[str] = Field(
        None,
        min_length=2,
        max_length=500,
        description="Dirección de la bodega",
        example="Av. Independencia No. 123, Col. Universidad, Toluca, México."
    )
    tipo: Optional[BodegaTipo] = Field(
        None,
        description="Tipo de bodega: 'small', 'large', 'large non-sortable'",
        example="large"
    )

# -----------------------------------------------------------------------------

class Puesto(str, Enum):
    """
    Enumeración de puestos válidos para un empleado.
    """
    operador = "operador bodega"
    coordinador = "coordinador"
    transportista = "transportista"

class Area(str, Enum):
    """
    Enumeración de áreas válidas de trabajo de un empleado.
    """
    bodega = "bodega"
    devoluciones = "devoluciones"
    soporte = "soporte logistico"

class EmpleadoBase(BaseModel):
    """
    Esquema base para un empleado.
    """
    nombre: str = Field(
        ..., 
        min_length=2,
        max_length=100,
        example="Juan"
    )
    apellido1: str = Field(
        ..., 
        min_length=2, 
        max_length=50, 
        example="Pérez"
    )
    apellido2: str = Field(
        ...,
        min_length=2,
        max_length=50,
        example="Gómez"
    )
    telefono: str = Field(
        ...,
        min_length=10,
        max_length=15,
        example="5512345678"
    )
    email: EmailStr = Field(
        ...,
        example="juan.perez1@empresa.com"
    )
    puesto: Puesto = Field(
        ...,
        description="Puestos de empleado: 'operador bodega', 'coordinador', 'transportista'",
        example="coordinador"
    )
    area: Area = Field(
        ...,
        description="Areas de trabajo: 'bodega', 'devoluciones', 'soporte logistico'",
        example="bodega"
    )

class EmpleadoCreate(EmpleadoBase):
    """
    Esquema para la creación de un empleado.
    Utiliza los mismos campos que EmpleadoBase, incluyendo contraseña.
    """
    contrasena: str = Field(
        ..., 
        min_length=8, 
        example="**********"
    )

class Empleado(EmpleadoBase):
    """
    Esquema de representación de un empleado con su ID.
    """
    empleado_id: int = Field(
        ...,
        description="ID único del empleado generado automáticamente."
    )

    class Config:
        from_attributes = True
        json_encoders = {
            'bytes': lambda v: v.decode('utf-8') if v else None,
            datetime: lambda v: v.isoformat()
        }
        fields = {
            'contrasena': {'exclude': True}
        }

class EmpleadoUpdate(BaseModel):
    """
    Esquema para la actualización parcial de un empleado.
    """
    nombre: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        example="Juan"
    )
    apellido1: Optional[str] = Field(
        None, 
        min_length=2, 
        max_length=50, 
        example="Pérez"
    )
    apellido2: Optional[str] = Field(
        None,
        min_length=2,
        max_length=50,
        example="Gómez"
    )
    telefono: Optional[str] = Field(
        None,
        min_length=10,
        max_length=15,
        example="5512345678"
    )
    email: Optional[EmailStr] = Field(
        None,
        example="juan.perez1@empresa.com"
    )
    puesto: Optional[Puesto] = Field(
        None,
        description="Puestos de empleado: 'operador bodega', 'coordinador', 'transportista'",
        example="coordinador"
    )
    area: Optional[Area] = Field(
        None,
        description="Areas de trabajo: 'bodega', 'devoluciones', 'soporte logistico'",
        example="bodega"
    )
    contrasena: Optional[str] = Field(
        None, 
        min_length=8, 
        example="**********"
    )

# -----------------------------------------------------------------------------

class EnvioBase(BaseModel):
    """
    Esquema base para un envío.
    """
    pedido_id: int = Field(
        ..., 
        gt=0,
        description="ID único del producto enviado (servicio externo).",
        example=1000
    )
    direccion_id: int = Field(
        ..., 
        gt=0,
        description="ID único de la dirección de entrega (servicio externo).",
        example=250
    )
    metodo_envio_id: int = Field(
        ...,
        gt=0,
        description="ID único del metodo de envio empleado.",
        example=3
    )

class EnvioCreate(EnvioBase):
    """
    Esquema para la creación de un envío.
    Utiliza los mismos campos que EnvioBase.
    """
    pass

class Envio(EnvioBase):
    """
    Esquema de representación de un envío completo con su ID.
    """
    envio_id: int  = Field(
        ...,
        description="ID único del envío generado automáticamente."
    )
    fecha_envio: datetime = Field(
        ...,
        description="Fecha y hora en la que el pedido fue enviado.",
        example="2025-06-25 14:30:00"
    )
    fecha_estimada_entrega: datetime = Field(
        ...,
        description="Fecha y hora estimmada de entrega.",
        example="2025-06-28 14:30:00"
    )
    codigo_rastreo: Optional[str] = Field(
        None, 
        min_length=8,
        max_length=20,
        example="ABCDEFGH123456789012"
    )

    class Config:
        from_attributes = True

class EnvioUpdate(BaseModel):
    """
    Esquema para la actualización parcial de un envio.
    """
    pedido_id: Optional[int] = Field(
        None, 
        gt=0,
        description="ID único del producto enviado (servicio externo).",
        example=1000
    )
    direccion_id: Optional[int] = Field(
        None, 
        gt=0,
        description="ID único de la dirección de entrega (servicio externo).",
        example=250
    )
    metodo_envio_id: Optional[int] = Field(
        None,
        gt=0,
        description="ID único del metodo de envio empleado.",
        example=3
    )
    fecha_envio: Optional[datetime] = Field(
        None,
        description="Fecha y hora en la que el pedido fue enviado.",
        example="2025-06-25 14:30:00"
    )
    fecha_estimada_entrega: Optional[datetime] = Field(
        None,
        description="Fecha y hora estimmada de entrega.",
        example="2025-06-28 14:30:00"
    )
    codigo_rastreo: Optional[str] = Field(
        None, 
        min_length=8,
        max_length=20,
        example="ABCDEFGH123456789012"
    )

# -----------------------------------------------------------------------------

class EstadoEnvioEstado(str, Enum):
    """
    Enumeración de estados de un envio.
    """
    pendiente = "pendiente"
    en_ruta = "en ruta"
    entregado = "entregado"
    devuelto = "devuelto"

class EstadoEnvioBase(BaseModel):
    """
    Esquema base para el estado de un envío.
    """
    envio_id: int = Field(
        ..., 
        gt=0,
        description="ID único del envío.",
        example=100
    )
    estado: EstadoEnvioEstado = Field(
        ...,
        description="Estado del envío: 'pendiente', 'en ruta', 'entregado', 'devuelto'",
        example="entregado"
    )
    descripcion: Optional[str] = Field(
        None, 
        min_length=5, 
        max_length=500, 
        description="Descripción con información adicional del estado del envío.",
        example="En camino al centro de distribución."
    )
    empleado_id: Optional[int] = Field(
        None,
        gt=0,
        description="ID único del empleado que registró el estado.",
        example=75
    )

class EstadoEnvioCreate(EstadoEnvioBase):
    """
    Esquema para crear un nuevo estado de envío.
    Utiliza los mismos campos que EstadoEnvioBase.
    """
    pass

class EstadoEnvio(EstadoEnvioBase):
    """
    Esquema de representación de un estado de un envio con su ID.
    """
    estado_envio_id: int = Field(
        ...,
        description="ID único del estado de envío generado automáticamente."
    )
    fecha: datetime = Field(
        ...,
        description="Fecha y hora del cambio de estado del envío.",
        example="2025-06-28 14:30:00"
    )

    class Config:
        from_attributes = True

class EstadoEnvioUpdate(BaseModel):
    """
    Esquema para la actualización parcial del estado de un envio.
    """
    envio_id: Optional[int] = Field(
        None, 
        gt=0,
        description="ID único del envio.",
        example=100
    )
    estado: Optional[EstadoEnvioEstado] = Field(
        None,
        description="Estado del envio: 'pendiente', 'en ruta', 'entregado', 'devuelto'",
        example="entregado"
    )
    descripcion: Optional[str] = Field(
        None, 
        min_length=5, 
        max_length=500, 
        description="Descripción con información adicional del estado del envío.",
        example="En camino al centro de distribución."
    )
    fecha: Optional[datetime] = Field(
        None,
        description="Fecha y hora del cambio de estado del envío.",
        example="2025-06-28 14:30:00"
    )
    empleado_id: Optional[int] = Field(
        None,
        gt=0,
        description="ID único del empleado que registró el estado.",
        example=75
    )

# -----------------------------------------------------------------------------

class DevolucionEstado(str, Enum):
    """
    Enumeración de los estados de una devolución.
    """
    pendiente = "pendiente"
    enviado = "enviado"
    recibido = "recibido"

class DevolucionBase(BaseModel):
    """
    Esquema base para una devolución.
    """
    envio_id: int = Field(
        ..., 
        gt=0,
        description="ID único del envío al que pertenece la devolución.",
        example=100
    )
    motivo: str = Field(
        ..., 
        min_length=5, 
        max_length=500, 
        description="Descripción del motivo de la devolución.",
        example="Producto incorrecto"
    )

class DevolucionCreate(DevolucionBase):
    """
    Esquema para la creación de una devolución.
    Utiliza los mismos campos que DevolucionBase.
    """
    pass

class Devolucion(DevolucionBase):
    """
    Esquema de representación de una devolución completa.
    """
    devolucion_id: int = Field(
        ..., 
        gt=0,
        description="ID único de la devolución generado automáticamente.",
        example=100
    )
    fecha: datetime = Field(
        ...,
        description="Fecha y hora de inicio del proceso de devolución.",
        example="2025-06-28 14:30:00"
    )
    estado: DevolucionEstado = Field(
        ...,
        description="Estados posibles de la devolución: 'pendiente', 'enviado', 'recibido'",
        example="enviado"
    )

    class Config:
        from_attributes = True

class DevolucionUpdate(BaseModel):
    """
    Esquema para la actualización parcial de una devolución.
    """
    envio_id: Optional[int] = Field(
        None, 
        gt=0,
        description="ID único del envío al que pertenece la devolución.",
        example=100
    )
    motivo: Optional[str] = Field(
        None, 
        min_length=5, 
        max_length=500, 
        description="Descripción del motivo de la devolución.",
        example="Producto incorrecto"
    )
    fecha: Optional[datetime] = Field(
        None,
        description="Fecha y hora de inicio del proceso de devolución.",
        example="2025-06-28 14:30:00"
    )
    estado: Optional[DevolucionEstado] = Field(
        None,
        description="Estados posibles de la devolución: 'pendiente', 'enviado', 'recibido'",
        example="enviado"
    )

# -----------------------------------------------------------------------------

class DevolucionDetalleBase(BaseModel):
    """
    Esquema base para el detalle de una devolución.
    """
    devolucion_id: int = Field(
        ..., 
        gt=0,
        description="ID único de la devolución.",
        example=100
    )
    producto_id: int = Field(
        ..., 
        gt=0,
        description="ID único del producto que se está devolviendo.",
        example=200
    )
    cantidad: int = Field(
        ..., 
        gt=0, 
        description="Cantidad del producto que se está devolviendo.",
        example=1
    )

class DevolucionDetalleCreate(DevolucionDetalleBase):
    """
    Esquema para la creación del detalle de una devolución.
    Utiliza los mismos campos que DevolucionDetalleBase.
    """
    pass

class DevolucionDetalle(DevolucionDetalleBase):
    """
    Esquema para representar un detalle de una devolución con su ID.
    """
    devolucion_detalle_id: int = Field(
        ..., 
        gt=0,
        description="ID único del detalle de una devolución generado automáticamente.",
        example=100
    )

    class Config:
        from_attributes = True

class DevolucionDetalleUpdate(BaseModel):
    """
    Esquema para la actualización parcial de un detalle de una devolución.
    """
    devolucion_id: Optional[int] = Field(
        None, 
        gt=0,
        description="ID único de la devolución.",
        example=100
    )
    producto_id: Optional[int] = Field(
        None, 
        gt=0,
        description="ID único del producto que se está devolviendo.",
        example=200
    )
    cantidad: Optional[int] = Field(
        None, 
        gt=0, 
        description="Cantidad del producto que se está devolviendo.",
        example=1
    )

# -----------------------------------------------------------------------------

class LogBodegaBase(BaseModel):
    """
    Esquema base para un registro de ingresos de productos en una bodega.
    """
    producto_id: int = Field(
        ..., 
        gt=0,
        description="ID único de un producto (externo).",
        example=100
    )
    cantidad: int = Field(
        ..., 
        gt=0, 
        description="Cantidad del producto que se está ingresando a la bodega.",
        example=10
    )
    bodega_id: int = Field(
        ..., 
        gt=0,
        description="ID único de la bodega a la que se ingresa el producto.",
        example=1
    )
    empleado_id: int = Field(
        ..., 
        gt=0,
        description="ID único del empleado que ingresa el producto a la bodega.",
        example=100
    )

class LogBodegaCreate(LogBodegaBase):
    """
    Esquema para la creación de un log de bodega.
    Utiliza los mismos campos que LogBodegaBase.
    """
    pass

class LogBodega(LogBodegaBase):
    """
    Esquema de representación de un ingreso de productos en bodega completo.
    """
    log_bodega_id: int = Field(
        ..., 
        gt=0,
        description="ID único del ingreso del producto en la bodega.",
        example=100
    )
    fecha: datetime = Field(
        ...,
        description="Fecha y hora del ingreso del producto en la bodega.",
        example="2025-06-28 14:30:00"
    )

    class Config:
        from_attributes = True

class LogBodegaUpdate(BaseModel):
    """
    Esquema para la actualización parcial de un ingresos de productos en una bodega.
    """
    producto_id: Optional[int] = Field(
        None, 
        gt=0,
        description="ID único de un producto (externo).",
        example=100
    )
    cantidad: Optional[int] = Field(
        None, 
        gt=0, 
        description="Cantidad del producto que se está ingresando a la bodega.",
        example=10
    )
    fecha: Optional[datetime] = Field(
        None,
        description="Fecha y hora del ingreso del producto en la bodega.",
        example="2025-06-28 14:30:00"
    )
    bodega_id: Optional[int] = Field(
        None, 
        gt=0,
        description="ID único de la bodega a la que se ingresa el producto.",
        example=1
    )
    empleado_id: Optional[int] = Field(
        None, 
        gt=0,
        description="ID único del empleado que ingresa el producto a la bodega.",
        example=100
    )

# -----------------------------------------------------------------------------

class Token(BaseModel):
    """
    Esquema para la respuesta de autenticación.

    Attributes:
        access_token (str): Token JWT utilizado para autenticar solicitudes.
        token_type (str): Tipo del token, usualmente 'bearer'.
    """
    access_token: str = Field(
        ..., 
        description="Token JWT de acceso otorgado tras autenticación exitosa.", 
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    )
    token_type: str = Field(
        ..., 
        description="Tipo del token de autenticación.", 
        example="bearer"
    )

class TokenData(BaseModel):
    """
    Esquema para los datos contenidos en el token JWT.

    Attributes:
        email (str): Email del usuario a autentificar.
        password (str): Contraseña del usuario a autentificar.
    """
    email: str = Field(
        ...,
        description="Correo electrónico del usuario a autentificar.", 
        example="usuario@ejemplo.com"
    )
    password: str = Field(
        ...,
        description="Contraseña del usuario a autentificar.",
        example="**********"
    )
