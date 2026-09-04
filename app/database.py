import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./restaurant_app.db")


if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, 
        connect_args={"check_same_thread": False},
        echo=False 
    )
else:
    
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, 
        pool_pre_ping=True, 
        pool_size=5,
        max_overflow=10
    )


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """
    All models will inherit from this Base class. 
    It maintains a metadata catalog of all your tables.
    """
    pass


def get_db():
    """
    Creates a new database session for a request and closes it when the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()