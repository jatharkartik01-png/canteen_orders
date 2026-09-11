from pathlib import Path
import mimetypes
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.database import engine, Base
import app.models 
from app.views.admin.admin import admin_router
from app.views.auth.auth import auth_router
from app.views.client.client import client_route

mimetypes.add_type("text/css", ".css")
mimetypes.add_type("image/webp", ".webp")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up... Creating database tables.")
    Base.metadata.create_all(bind=engine)
    yield 
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)

# Enable session support across all routes
app.add_middleware(
    SessionMiddleware,
    secret_key="your-secret-key-goes-here",  # Replace with a strong secret key
    max_age=14400,                            # 4 hours session expiration
    https_only=False,                         # Set to True when deploying with HTTPS
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(client_route)