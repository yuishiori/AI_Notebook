from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas
from ..dependencies import create_access_token, get_current_user
from google.oauth2 import id_token
from google.auth.transport import requests
import os
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["auth"])

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")

class GoogleAuthRequest(BaseModel):
    id_token: str

@router.post("/google", response_model=schemas.Token)
async def google_auth(auth_data: GoogleAuthRequest, db: Session = Depends(get_db)):
    try:
        # 1. Verify the Google ID Token
        id_info = id_token.verify_oauth2_token(auth_data.id_token, requests.Request(), GOOGLE_CLIENT_ID)
        
        email = id_info['email']
        
        # --- 白名單檢查 (方案 A) ---
        allowed_users_str = os.environ.get("ALLOWED_USERS", "")
        if allowed_users_str:
            allowed_list = [e.strip() for e in allowed_users_str.split(",")]
            if email not in allowed_list:
                print(f"DEBUG: Unauthorized login attempt from: {email}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail=f"User {email} is not authorized to use this system."
                )
        # ------------------------

        name = id_info.get('name')
        picture = id_info.get('picture')
        
        # 2. Find or create User
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            user = models.User(
                email=email,
                name=name,
                picture_url=picture
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # 3. Seed default workspaces for new user
            ws_work = models.Workspace(name="工作", owner_id=user.id)
            ws_life = models.Workspace(name="生活", owner_id=user.id)
            db.add(ws_work)
            db.add(ws_life)
            db.commit()
            
        # 4. Generate JWT
        access_token = create_access_token(data={"user_id": user.id})
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"DEBUG: Google Auth Failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Google authentication failed: {str(e)}")

@router.get("/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user
