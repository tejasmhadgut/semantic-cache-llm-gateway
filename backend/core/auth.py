from datetime import datetime, timedelta, timezone
from core.config import settings
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain:str, hashed:str) -> bool:
    return pwd_context.verify(plain,hashed)


def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials  = Security(security)):
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid Token")
        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid Token")