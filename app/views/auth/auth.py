from fastapi import APIRouter, Form, Depends, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import EmailStr
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole


router = APIRouter()
hash = PasswordHash.recommended()
templates = Jinja2Templates(directory="app/templates/auth")


# ==========================================
# LOGIN ROUTES
# ==========================================

@router.get("/")
def login_page(request: Request):
    """Renders the HTML Login Page (GET /)"""
    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )


@router.post("/login")
def login(
    email: EmailStr = Form(),
    password: str = Form(),
    db: Session = Depends(get_db)
):
    """Processes Login Form Submission (POST /login)"""
    user = db.query(User).filter(User.user_email == email).first()

    if not user or not hash.verify(password, user.hashed_pwd):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    return {"Message": "Login successful", "user_id": user.user_id}


# ==========================================
# REGISTER ROUTES
# ==========================================

@router.get("/register")
def register_page(request: Request):
    """Renders the HTML Registration Page (GET /register)"""
    return templates.TemplateResponse(
        request=request,
        name="register.html"
    )


@router.post("/register")
def register_usr(
    username: str = Form(),
    password: str = Form(),
    mobile: str = Form(),
    email: EmailStr = Form(),
    db: Session = Depends(get_db)
):
    """Processes Registration Form Submission (POST /register)"""
    existing_user = db.query(User).filter(User.user_email == email).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists."
        )
    
    password_hashed = hash.hash(password)
    
    new_user = User(
        username=username,
        user_email=email,
        hashed_pwd=password_hashed,
        user_mobile=mobile,
        user_role=UserRole.CLIENT
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"Message": "User successfully registered", "user_id": new_user.user_id}