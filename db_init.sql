-- Creación de la base de datos
CREATE DATABASE IF NOT EXISTS microservicio_logistica 
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;
USE microservicio_logistica;

-- Creación del usuario
CREATE USER IF NOT EXISTS 'logistics_user'@'%' IDENTIFIED BY 'logistics_password';

-- Concesión de permisos
GRANT ALL PRIVILEGES ON microservicio_logistica.* TO 'logistics_user'@'%';
FLUSH PRIVILEGES;

-- Tabla metodo_envio
CREATE TABLE IF NOT EXISTS metodo_envio (
    metodo_envio_id INT AUTO_INCREMENT PRIMARY KEY,
    tipo            ENUM('estandar', 'rapido', 'express') NOT NULL,
    descripcion     TEXT NOT NULL,
    tiempo_estimado INT NOT NULL COMMENT 'Días estimados para entrega',
    costo           DECIMAL(6,2) NOT NULL
);

-- Tabla bodega
CREATE TABLE IF NOT EXISTS bodega (
    bodega_id        INT AUTO_INCREMENT PRIMARY KEY,
    direccion_bodega TEXT NOT NULL,
    tipo             ENUM('small', 'large', 'large non-sortable') NOT NULL
);

-- Tabla empleado
CREATE TABLE IF NOT EXISTS empleado (
    empleado_id INT AUTO_INCREMENT PRIMARY KEY,
    contrasena  VARCHAR(255) NOT NULL,
    nombre      VARCHAR(100) NOT NULL,
    apellido1   VARCHAR(50) NOT NULL,
    apellido2   VARCHAR(50) NOT NULL,
    telefono    VARCHAR(15) NOT NULL,
    email       VARCHAR(100) NOT NULL,
    puesto      ENUM('operador bodega', 'coordinador', 'transportista') NOT NULL,
    area        ENUM('bodega', 'devoluciones', 'soporte logistico') NOT NULL
);

-- Tabla envio
CREATE TABLE IF NOT EXISTS envio (
    envio_id               INT AUTO_INCREMENT PRIMARY KEY,
    pedido_id              INT NOT NULL,
    direccion_id           INT NOT NULL,
    metodo_envio_id        INT NOT NULL,
    fecha_envio            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_estimada_entrega DATETIME,
    codigo_rastreo         VARCHAR(20) UNIQUE,
    FOREIGN KEY (metodo_envio_id) REFERENCES metodo_envio(metodo_envio_id)
);

-- Tabla estado_envio
CREATE TABLE IF NOT EXISTS estado_envio (
    estado_envio_id INT AUTO_INCREMENT PRIMARY KEY,
    envio_id        INT NOT NULL,
    estado          ENUM('pendiente', 'en ruta', 'entregado', 'devuelto') NOT NULL,
    descripcion     TEXT,
    fecha           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    empleado_id     INT,
    FOREIGN KEY (envio_id) REFERENCES envio(envio_id),
    FOREIGN KEY (empleado_id) REFERENCES empleado(empleado_id)
);

-- Tabla devolucion
CREATE TABLE IF NOT EXISTS devolucion (
    devolucion_id INT AUTO_INCREMENT PRIMARY KEY,
    envio_id      INT NOT NULL,
    motivo        TEXT NOT NULL,
    fecha         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado        ENUM('pendiente', 'enviado', 'recibido') NOT NULL DEFAULT 'pendiente',
    FOREIGN KEY (envio_id) REFERENCES envio(envio_id)
);

-- Tabla devolucion_detalle
CREATE TABLE IF NOT EXISTS devolucion_detalle (
    devolucion_detalle_id INT AUTO_INCREMENT PRIMARY KEY,
    devolucion_id         INT NOT NULL,
    producto_id           INT NOT NULL,
    cantidad              INT NOT NULL,
    FOREIGN KEY (devolucion_id) REFERENCES devolucion(devolucion_id)
);

-- Tabla log_bodega
CREATE TABLE IF NOT EXISTS log_bodega (
    log_bodega_id INT AUTO_INCREMENT PRIMARY KEY,
    producto_id   INT NOT NULL,
    cantidad      INT NOT NULL,
    fecha         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    bodega_id     INT NOT NULL,
    empleado_id   INT NOT NULL,
    FOREIGN KEY (bodega_id) REFERENCES bodega(bodega_id),
    FOREIGN KEY (empleado_id) REFERENCES empleado(empleado_id)
);

-- Trigger para calcular fecha_estimada_entrega al insertar en envio
DROP TRIGGER IF EXISTS calcular_fecha_entrega;
DELIMITER //
CREATE TRIGGER calcular_fecha_entrega
BEFORE INSERT ON envio
FOR EACH ROW
BEGIN
    DECLARE dias_estimados INT;
    
    SELECT tiempo_estimado INTO dias_estimados
    FROM metodo_envio
    WHERE metodo_envio_id = NEW.metodo_envio_id;
    
    SET NEW.fecha_estimada_entrega = DATE_ADD(NOW(), INTERVAL dias_estimados DAY);
END//
DELIMITER ;

-- Trigger para actualizar estado_envio cuando devolución es recibida
DROP TRIGGER IF EXISTS actualizar_estado_devolucion;
DELIMITER //
CREATE TRIGGER actualizar_estado_devolucion
AFTER UPDATE ON devolucion
FOR EACH ROW
BEGIN
    IF NEW.estado = 'recibido' AND OLD.estado != 'recibido' THEN
        INSERT INTO estado_envio (envio_id, estado, descripcion, fecha)
        VALUES (
            NEW.envio_id, 
            'devuelto', 
            'Producto devuelto recibido en bodega', 
            NOW()
        );
    END IF;
END//
DELIMITER ;
