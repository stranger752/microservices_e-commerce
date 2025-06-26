import time
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.api import shipping_method, warehouse, employee, shipping,  shipping_status, returns, returns_details, warehouse_log

app = FastAPI(title="Logistics Service API")

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Intenta conectarse a la base de datos con reintentos
def wait_for_db():
    engine = create_engine(
        "mysql+pymysql://logistics_user:logistics_password@logistics_db/microservicio_logistica?connect_timeout=10&charset=utf8mb4",
        connect_args={"init_command": "SET NAMES utf8mb4"}
    )
    retries = 5
    delay = 5
    
    while retries > 0:
        try:
            connection = engine.connect()
            connection.close()
            return engine
        except OperationalError as e:
            print(f"Error de conexión a la base de datos: {e}")
            print(f"Reintentando en {delay} segundos... ({retries} intentos restantes)")
            retries -= 1
            time.sleep(delay)
    
    raise Exception("No se pudo conectar a la base de datos después de varios intentos")

@app.on_event("startup")
async def startup():
    try:
        engine = wait_for_db()
        # Base.metadata.create_all(bind=engine)
        print("Conexión a DB exitosa")
    except Exception as e:
        print(f"Error durante el startup: {e}")
        raise

# Incluir routers
app.include_router(shipping_method.router)
app.include_router(warehouse.router)
app.include_router(employee.router)
app.include_router(shipping.router)
app.include_router(shipping_status.router)
app.include_router(returns.router)
app.include_router(returns_details.router)
app.include_router(warehouse_log.router)


@app.get("/")
async def root():
    return {"message": "Logistics Service API - Sistema de gestión de envíos y logística"}