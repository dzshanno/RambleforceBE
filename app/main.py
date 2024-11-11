from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, attendees, merchandise, events, comments
from app.database.session import engine
from app.database.models import Base
from app.utils.config import Settings

# Create database tables if they do not exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Rambleforce25 API",
    description="Backend API for Rambleforce25 Salesforce Netwalking Event",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(attendees.router, prefix="/api/v1/attendees", tags=["attendees"])
app.include_router(
    merchandise.router, prefix="/api/v1/merchandise", tags=["merchandise"]
)
app.include_router(events.router, prefix="/api/v1/events", tags=["events"])
app.include_router(comments.router, prefix="/api/v1/comments", tags=["comments"])


@app.get("/")
async def root():
    return {"message": "Welcome to Rambleforce25 API"}
