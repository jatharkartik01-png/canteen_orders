# app/views/auth/auth.py

from datetime import datetime, timezone, timedelta
import secrets

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    Request,
    status,
)
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole
from app.services.email import send_reset_email
# Import the unified hashing utility
from app.auth_utils import hash as hash_pwd, verify as verify_pwd 

auth_router = APIRouter(tags=["Authentication"])
templates = Jinja2Templates(directory="app/templates/auth")


def is_token_expired(expires_at: datetime | None) -> bool:
    """Safely checks if a database reset token timestamp has expired."""
    if not expires_at:
        return True
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at < datetime.now(timezone.utc)


@auth_router.get("/")
def login_page(request: Request):
    """Renders the HTML Login Page (GET /)"""
    return templates.TemplateResponse(request=request, name="login.html")


@auth_router.post("/login")
def login(
    request: Request,
    email: EmailStr = Form(),
    password: str = Form(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.user_email == email).first()

    # Use the unified verify method
    if not user or not verify_pwd(password, user.hashed_pwd):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Invalid email or password."},
        )

    # Store user session data
    request.session["user_id"] = user.user_id
    
    # Redirect directly to the main portal homepage
    return RedirectResponse(url="/home", status_code=status.HTTP_303_SEE_OTHER)


@auth_router.get("/register")
def register_page(request: Request):
    """Renders the HTML Registration Page (GET /register)"""
    return templates.TemplateResponse(request=request, name="register.html")


@auth_router.post("/register")
def register_usr(
    request: Request,
    username: str = Form(),
    password: str = Form(),
    mobile: str = Form(),
    email: EmailStr = Form(),
    db: Session = Depends(get_db),
):
    """Processes Registration Form Submission (POST /register)"""
    existing_user = db.query(User).filter(User.user_email == email).first()

    if existing_user:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": "User with this email already exists."},
        )

    # Use the unified hash method
    password_hashed = hash_pwd(password)

    try:
        new_user = User(
            username=username,
            user_email=email,
            hashed_pwd=password_hashed,
            user_mobile=mobile,
            user_role=UserRole.CLIENT,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception:
        db.rollback()
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": "Registration failed due to a database error."},
        )

    # Save session & redirect to home page
    request.session["user_id"] = new_user.user_id
    return RedirectResponse(url="/home", status_code=status.HTTP_303_SEE_OTHER)


@auth_router.get("/logout")
def logout(request: Request):
    """Clears user session and redirects to login page"""
    request.session.clear()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@auth_router.get("/forgot-password")
async def forgot_password_page(request: Request):
    """Renders Forgot Password Page"""
    return templates.TemplateResponse(request=request, name="forgot_password.html")


@auth_router.post("/forgot-password")
async def process_forgot_password(
    background_tasks: BackgroundTasks,
    request: Request,
    email: EmailStr = Form(...),
    db: Session = Depends(get_db),
):
    """Handles Forgot Password Form Submission and triggers reset email"""
    user = db.query(User).filter(User.user_email == email).first()
    
    # Generic success response to prevent email enumeration attacks
    if user:
        token = secrets.token_urlsafe(32)
        expires = datetime.now(timezone.utc) + timedelta(minutes=15)

        user.reset_token = token
        user.reset_token_expires = expires
        db.commit()

        reset_url = f"{request.base_url}reset-password?token={token}"
        background_tasks.add_task(send_reset_email, email, reset_url)

    return templates.TemplateResponse(
        request=request,
        name="forgot_password.html",
        context={"message": "If that email exists, a password reset link has been sent."},
    )


@auth_router.get("/reset-password")
async def reset_password_page(
    request: Request, token: str, db: Session = Depends(get_db)
):
    """Renders Reset Password Page on GET request"""
    user = db.query(User).filter(User.reset_token == token).first()
    if not user or is_token_expired(user.reset_token_expires):
        return templates.TemplateResponse(
            request=request,
            name="reset_password.html",
            context={"error": "Invalid or expired reset token.", "token": None},
        )

    return templates.TemplateResponse(
        request=request, name="reset_password.html", context={"token": token}
    )


@auth_router.post("/reset-password")
async def process_reset_password(
    request: Request,
    token: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Handles password update on POST request"""
    user = db.query(User).filter(User.reset_token == token).first()

    if not user or is_token_expired(user.reset_token_expires):
        return templates.TemplateResponse(
            request=request,
            name="reset_password.html",
            context={"error": "Invalid or expired reset token.", "token": None},
        )

    # Use unified hash method
    user.hashed_pwd = hash_pwd(password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()

    return RedirectResponse(
        url="/?reset=success", status_code=status.HTTP_303_SEE_OTHER
    )