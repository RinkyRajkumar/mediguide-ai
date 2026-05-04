from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Doctor, DoctorAvailability, User
from app.security import get_current_user
from app.services.appointment_service import doctor_query, generate_available_slots, serialize_slot

router = APIRouter(prefix="/api/doctors", tags=["Doctors and Availability"])


@router.get("")
def get_doctors(
    specialization: str = "",
    location: str = "",
    language: str = "",
    gender: str = "any",
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doctors = doctor_query(db, specialization, location, language, gender).all()
    return [
        {
            "id": doctor.id,
            "name": doctor.name,
            "specialization": doctor.specialization,
            "location": doctor.location,
            "gender": doctor.gender,
            "languages": doctor.languages.split(","),
        }
        for doctor in doctors
    ]


@router.get("/{doctor_id}/availability")
def get_availability(
    doctor_id: str,
    from_datetime: datetime | None = None,
    duration_minutes: int = 30,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doctor = db.get(Doctor, doctor_id)
    if doctor is None:
        return {"doctor_id": doctor_id, "availability": []}
    slots = generate_available_slots(db, [doctor], from_datetime or datetime.now(), duration_minutes)
    weekly = db.query(DoctorAvailability).filter(DoctorAvailability.doctor_id == doctor_id).all()
    return {
        "doctor_id": doctor_id,
        "working_hours": [{"weekday": item.weekday, "start_time": item.start_time, "end_time": item.end_time} for item in weekly],
        "availability": [serialize_slot(slot) for slot in slots[:20]],
    }
