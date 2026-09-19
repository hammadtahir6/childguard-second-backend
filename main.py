from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth, bands, children, locations, vitals, alerts

# Create all database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ChildGuard API",
    description="AI-Powered Child Safety Wearable System",
    version="1.0.0",
    docs_url="/docs",
)

# CORS — allows React Native app to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth.router)
app.include_router(children.router)
app.include_router(vitals.router)
app.include_router(alerts.router)
app.include_router(bands.router)       
app.include_router(locations.router)

@app.get("/")
def root():
    return {
        "app": "ChildGuard API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}