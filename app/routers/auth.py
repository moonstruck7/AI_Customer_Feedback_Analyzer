from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import UserResponse, UserLogin

router = APIRouter(prefix="/api/auth", tags=["Authentication & Roles"])

@router.get("/users", response_model=list[UserResponse])
def get_available_users(db: Session = Depends(get_db)):
    """
    Returns available system users for easy role switching (SMB Owner, Support Manager, System Admin).
    """
    users = db.query(User).all()
    return users

@router.post("/login", response_model=UserResponse)
def login_user(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user credentials")
    return user
