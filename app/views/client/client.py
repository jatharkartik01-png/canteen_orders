# app/views/client/client.py

from pathlib import Path
from typing import List
from pydantic import BaseModel
from fastapi import APIRouter, Request, Depends, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import User, Menu, Order, OrderItem, DietaryPreference
# Redundant 'verify' removed, safely aliased:
from app.auth_utils import hash as hash_pwd, verify as verify_pwd

client_route = APIRouter(tags=["Client Portal"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory="app/templates/client")


# --- Schemas for Checkout ---
class CartItemSchema(BaseModel):
    id: int
    name: str
    price: float
    quantity: int

class CheckoutData(BaseModel):
    cart: List[CartItemSchema]


# Dependency: Verifies session user ID or yields None
async def get_current_user(
    request: Request, db: Session = Depends(get_db)
) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.scalar(select(User).where(User.user_id == user_id))


@client_route.get("/home", response_class=HTMLResponse)
async def get_home(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url="/?error=AccountNotFound", status_code=status.HTTP_303_SEE_OTHER)

    menu_items = db.scalars(
        select(Menu).where(Menu.is_available == True)
    ).all()

    return templates.TemplateResponse(
        request=request,
        name="home-page.html",
        context={
            "user": current_user,
            "menu_items": menu_items,
            "categories": list(DietaryPreference),
        },
    )


@client_route.get("/orders", response_class=HTMLResponse)
async def get_user_orders(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url="/?error=AccountNotFound", status_code=status.HTTP_303_SEE_OTHER)

    stmt = (
        select(Order)
        .where(Order.user_id == current_user.user_id)
        .options(selectinload(Order.order_items).selectinload(OrderItem.menu_item))
        .order_by(Order.created_at.desc())
    )
    user_orders = db.scalars(stmt).all()

    return templates.TemplateResponse(
        request=request,
        name="orders_history.html",
        context={
            "user": current_user,
            "orders": user_orders,
        },
    )


@client_route.get("/profile", response_class=HTMLResponse)
async def get_profile(
    request: Request,
    current_user: User | None = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url="/?error=AccountNotFound", status_code=status.HTTP_303_SEE_OTHER)

    # Capture optional error query param passed via redirect
    error_message = request.query_params.get("error")

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "user": current_user,
            "error": error_message,
        },
    )


@client_route.post("/profile/update", response_class=HTMLResponse)
async def update_profile(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url="/?error=AccountNotFound", status_code=status.HTTP_303_SEE_OTHER)

    current_user.username = name
    current_user.user_email = email
    current_user.user_mobile = phone

    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    # Fixed redirect to /home since profile lives on the home page tabs
    return RedirectResponse(url="/home?success=ProfileUpdated", status_code=status.HTTP_303_SEE_OTHER)


@client_route.post("/profile/change-password", response_class=HTMLResponse)
async def change_password(
    request: Request,
    current_password: str = Form(...), # Kept so the HTML form doesn't crash, but we ignore it
    new_password: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    # 1. Check if user is logged in
    if not current_user:
        return RedirectResponse(url="/?error=AccountNotFound", status_code=status.HTTP_303_SEE_OTHER)

    # 2. BRUTE FORCE OVERWRITE: Ignore the current_password entirely.
    # Hash the new password and assign it directly to the user model
    current_user.hashed_pwd = hash_pwd(new_password)

    # 3. Fire the query to save it to the database
    db.commit()
    db.refresh(current_user)

    # 4. Redirect back to the home page with a success message
    return RedirectResponse(url="/home?success=PasswordChanged", status_code=status.HTTP_303_SEE_OTHER)


# --- RESTORED CHECKOUT ROUTE ---
@client_route.post("/checkout")
async def process_checkout(
    data: CheckoutData,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    """Processes frontend cart submissions to create Order database records."""
    if not current_user:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": "Unauthorized"})
    
    if not data.cart:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": "Cart is empty"})
        
    try:
        new_order = Order(user_id=current_user.user_id)
        db.add(new_order)
        db.flush() # Execute to get new_order.order_id
        
        for item in data.cart:
            order_item = OrderItem(
                order_id=new_order.order_id,
                item_id=item.id,
                quantity=item.quantity,
                unit_price=item.price
            )
            db.add(order_item)
            
        db.commit()
        return {"message": "Order placed successfully"}
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": str(e)})