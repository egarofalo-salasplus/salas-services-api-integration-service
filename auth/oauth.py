# auth/oauth.py
import os
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from decouple import config


# Definir una clave secreta para firmar el JWT
SECRET_KEY = config('SALAS_API_KEY', default=os.getenv('SALAS_API_KEY'))


# Inicializa el esquema de autenticación HTTPBearer
bearer_scheme = HTTPBearer()

# Excepción de credenciales
def credentials_exception() -> HTTPException:
    """
    Genera una excepción de credenciales para la autenticación fallida.

    Retorna
    -------
    HTTPException
        Excepción HTTP con código de estado 401.
    """
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales no válidas",
        headers={"WWW-Authenticate": "Bearer"},
    )


# Función para verificar el Bearer Token
async def verify_secret_key(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    if token != SECRET_KEY:
        raise credentials_exception
    return token