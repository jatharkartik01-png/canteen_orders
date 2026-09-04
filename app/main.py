from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles  # Added import

# 1. Import database engine and Base
from app.database import engine, Base
# 2. IMPORTANT: You must import your models here so SQLAlchemy knows they exist!
import app.models 

from app.views.auth.auth import router


# 3. Define the lifespan event
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up... Creating database tables.")
    Base.metadata.create_all(bind=engine)
    
    yield 
    
    print("Shutting down...")


# 4. Initialize app and attach lifespan
app = FastAPI(lifespan=lifespan)

# 5. Include router and mount static files directory
app.include_router(router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")