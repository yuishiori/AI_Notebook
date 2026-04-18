from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from .database import get_db
from . import models, schemas
from .config import settings
from typing import Optional, List, Dict, Any
from .ai.gemini_client import get_gemini_client, TOOL_DEFINITIONS
import os

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/google")

# Load secret key from environment
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "fallback-secret-key-for-dev-only")
ALGORITHM = "HS256"

def create_access_token(data: dict):
    to_encode = data.copy()
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        token_data = schemas.TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception
    return user

def get_gemini():
    return get_gemini_client()

def get_tools():
    return TOOL_DEFINITIONS
