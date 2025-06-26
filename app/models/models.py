from sqlalchemy import Column, Integer, String, Enum, Text, DateTime, ForeignKey, DECIMAL, TIMESTAMP
from sqlalchemy.orm import relationship
from app.database import Base

class MetodoEnvio(Base):
    __tablename__ = "metodo_envio"
    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_0900_ai_ci"
    }
    
    metodo_envio_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tipo = Column(Enum('estandar', 'rapido', 'express'), nullable=False)
    descripcion = Column(Text, nullable=False)
    tiempo_estimado = Column(Integer, nullable=False, comment="Días estimados para entrega")
    costo = Column(DECIMAL(6,2), nullable=False)
    
    envios = relationship("Envio", back_populates="metodo_envio")

class Bodega(Base):
    __tablename__ = "bodega"
    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_0900_ai_ci"
    }
    
    bodega_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    direccion_bodega = Column(Text, nullable=False)
    tipo = Column(Enum('small', 'large', 'large non-sortable'), nullable=False)
    
    logs = relationship("LogBodega", back_populates="bodega")

class Empleado(Base):
    __tablename__ = "empleado"
    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_0900_ai_ci"
    }
    
    empleado_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    contrasena = Column(String(255), nullable=False)
    nombre = Column(String(100), nullable=False)
    apellido1 = Column(String(50), nullable=False)
    apellido2 = Column(String(50), nullable=False)
    telefono = Column(String(15), nullable=False)
    email = Column(String(100), nullable=False)
    puesto = Column(Enum('operador bodega', 'coordinador', 'transportista'), nullable=False)
    area = Column(Enum('bodega', 'devoluciones', 'soporte logistico'), nullable=False)
    
    estados_envio = relationship("EstadoEnvio", back_populates="empleado")
    logs_bodega = relationship("LogBodega", back_populates="empleado")

class Envio(Base):
    __tablename__ = "envio"
    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_0900_ai_ci"
    }
    
    envio_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pedido_id = Column(Integer, nullable=False)
    direccion_id = Column(Integer, nullable=False)
    metodo_envio_id = Column(Integer, ForeignKey("metodo_envio.metodo_envio_id"), nullable=False)
    fecha_envio = Column(DateTime, nullable=False, server_default="CURRENT_TIMESTAMP")
    fecha_estimada_entrega = Column(DateTime)
    codigo_rastreo = Column(String(20), unique=True)
    
    metodo_envio = relationship("MetodoEnvio", back_populates="envios")
    estados = relationship("EstadoEnvio", back_populates="envio")
    devoluciones = relationship("Devolucion", back_populates="envio")

class EstadoEnvio(Base):
    __tablename__ = "estado_envio"
    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_0900_ai_ci"
    }
    
    estado_envio_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    envio_id = Column(Integer, ForeignKey("envio.envio_id"), nullable=False)
    estado = Column(Enum('pendiente', 'en ruta', 'entregado', 'devuelto'), nullable=False)
    descripcion = Column(Text)
    fecha = Column(DateTime, nullable=False, server_default="CURRENT_TIMESTAMP")
    empleado_id = Column(Integer, ForeignKey("empleado.empleado_id"))
    
    envio = relationship("Envio", back_populates="estados")
    empleado = relationship("Empleado", back_populates="estados_envio")

class Devolucion(Base):
    __tablename__ = "devolucion"
    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_0900_ai_ci"
    }
    
    devolucion_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    envio_id = Column(Integer, ForeignKey("envio.envio_id"), nullable=False)
    motivo = Column(Text, nullable=False)
    fecha = Column(TIMESTAMP, nullable=False, server_default="CURRENT_TIMESTAMP")
    estado = Column(Enum('pendiente', 'enviado', 'recibido'), nullable=False, server_default="'pendiente'")
    
    envio = relationship("Envio", back_populates="devoluciones")
    detalles = relationship("DevolucionDetalle", back_populates="devolucion")

class DevolucionDetalle(Base):
    __tablename__ = "devolucion_detalle"
    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_0900_ai_ci"
    }
    
    devolucion_detalle_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    devolucion_id = Column(Integer, ForeignKey("devolucion.devolucion_id"), nullable=False)
    producto_id = Column(Integer, nullable=False)
    cantidad = Column(Integer, nullable=False)
    
    devolucion = relationship("Devolucion", back_populates="detalles")

class LogBodega(Base):
    __tablename__ = "log_bodega"
    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_0900_ai_ci"
    }
    
    log_bodega_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    producto_id = Column(Integer, nullable=False)
    cantidad = Column(Integer, nullable=False)
    fecha = Column(TIMESTAMP, nullable=False, server_default="CURRENT_TIMESTAMP")
    bodega_id = Column(Integer, ForeignKey("bodega.bodega_id"), nullable=False)
    empleado_id = Column(Integer, ForeignKey("empleado.empleado_id"), nullable=False)
    
    bodega = relationship("Bodega", back_populates="logs")
    empleado = relationship("Empleado", back_populates="logs_bodega")