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
    search: str = "",
    limit: int = 600,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doctors = doctor_query(db, specialization, location, language, gender).all()
    if search.strip():
        term = search.strip().lower()
        doctors = [
            doctor
            for doctor in doctors
            if term in doctor.name.lower()
            or term in doctor.specialization.lower()
            or term in doctor.location.lower()
            or term in doctor.languages.lower()
            or term in doctor.qualification.lower()
            or (doctor.clinic and term in doctor.clinic.name.lower())
            or (doctor.clinic and term in doctor.clinic.city.lower())
        ]
    doctors = doctors[: max(1, min(limit, 1000))]
    return [
        {
            "id": doctor.id,
            "name": doctor.name,
            "specialization": doctor.specialization,
            "location": doctor.location,
            "gender": doctor.gender,
            "languages": [item.strip() for item in doctor.languages.split(",") if item.strip()],
            "qualification": doctor.qualification,
            "experience_years": doctor.experience_years,
            "consultation_fee": doctor.consultation_fee,
            "rating": doctor.rating,
            "online_consultation": doctor.online_consultation.lower() == "true",
            "consultation_modes": doctor.consultation_modes,
            "appointment_duration_minutes": doctor.appointment_duration_minutes,
            "max_daily_appointments": doctor.max_daily_appointments,
            "preferred_patient_age_group": doctor.preferred_patient_age_group,
            "clinic": {
                "name": doctor.clinic.name if doctor.clinic else doctor.location,
                "city": doctor.clinic.city if doctor.clinic else "",
                "area": doctor.clinic.area if doctor.clinic else "",
                "address": doctor.clinic.address if doctor.clinic else "",
            },
            "about_doctor": doctor.about_doctor,
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
