# microservices_e-commerce

## API del microservicio de logística

### Descripción

Se usó Docker para facilitar el montaje. El sistema consiste de dos contenedores: un contenedor con una base de datos en MySQL y otro con FastAPI. Además, se configuró un volumen para persistencia.

### Configuración previa
- Verificar que los puertos 3306 y 8002 no se estén ocupando en su equipo. También se pueden cambiar los puertos a usar desde el archivo `docker-compose.yml`.

- Se requiere tener instalado `docker` y `docker-compose`.

### Creación de los contenedores

Para crear los contenedores basta con ejecutar el siguiente comando estando dentro de la carpeta que contiene el archivo `docker-compose.yml`:
```bash
docker-compose up --build
```

Posteriormente, la API se encontrará disponible en:
```plaintext
http://localhost:8002
```

Se puede interactuar directamente con la API desde una interface web en:
```plaintext
http://localhost:8002/docs
http://localhost:8002/redoc
```

### Configuración adicional de la base de datos

**Nota:** Los comandos siguientes solo funcionan si no se han modificado las credenciales definidas en el archivo `docker-compose.yml`. Además, verificar que el nombre del contenedor de la BD sea `microservices_e-commerce-main_logistics_db_1` o modificar los comandos con el nombre apropiado.

Para cargar los registros del archivo `dump_logistica.sql`, obtener el archivo y colocarlo en el directorio del proyecto. Después, ejecutar:
```bash
docker exec -i microservices_e-commerce-main_logistics_db_1 mysql -u root -prootpassword microservicio_logistica < dump_logistica.sql
```

En caso de ser necesario, se puede acceder al contenedor de MySQL con el comando siguiente:
```bash
docker exec -it microservices_e-commerce-main_logistics_db_1 mysql -u logistics_user -plogistics_password microservicio_logistica
```

