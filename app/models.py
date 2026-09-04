import enum
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import String, Numeric, ForeignKey, DateTime, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# --- ENUMS ---
class UserRole(str, enum.Enum):
    CLIENT = "CLIENT"
    ADMIN = "ADMIN"

class DietaryPreference(str, enum.Enum):
    VEGETARIAN = "VEGETARIAN"
    NON_VEGETARIAN = "NON-VEGETARIAN"
    EGGETARIAN = "EGGETARIAN"
    CARBONATED = "CARBONATED"
    MILK_BASED = "MILK BASED"

class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    PREPARING = "PREPARING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# --- MODELS ---
class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255))
    hashed_pwd: Mapped[str] = mapped_column(String(255))
    user_email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    user_role: Mapped[UserRole] = mapped_column(default=UserRole.CLIENT)
    user_mobile: Mapped[Optional[str]] = mapped_column(String(15))
    orders: Mapped[List["Order"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Menu(Base):
    __tablename__ = "menu"

    item_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    item_name: Mapped[str] = mapped_column(String(255), index=True)
    dietary_preference: Mapped[DietaryPreference]
    item_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    
    
    is_available: Mapped[bool] = mapped_column(
        default=True, server_default=text("true"), index=True
    )

    order_items: Mapped[List["OrderItem"]] = relationship(back_populates="menu_item")


class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), index=True)
    
    
    status: Mapped[OrderStatus] = mapped_column(
        default=OrderStatus.PENDING, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now(), index=True
    )

    user: Mapped["User"] = relationship(back_populates="orders")
    
    order_items: Mapped[List["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    order_item_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"), index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("menu.item_id"), index=True)
    
    quantity: Mapped[int] = mapped_column(default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    order: Mapped["Order"] = relationship(back_populates="order_items")
    menu_item: Mapped["Menu"] = relationship(back_populates="order_items")