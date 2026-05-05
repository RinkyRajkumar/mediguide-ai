from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routes import ai, appointments, auth, doctor, doctors, health, medications, patients, schedule_memory

app = FastAPI(
    title="MediGuide AI API",
    description="JWT-protected AI healthcare assistant API with agent, MCP, and skills architecture.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": settings.app_name}


@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "status": "running",
        "disclaimer": "MediGuide AI provides AI-assisted health information only and is not a replacement for a licensed medical professional.",
    }


app.include_router(auth.router)
app.include_router(doctor.router)
app.include_router(ai.router)
app.include_router(health.router)
app.include_router(appointments.router)
app.include_router(patients.router)
app.include_router(doctors.router)
app.include_router(medications.router)
app.include_router(schedule_memory.router)
