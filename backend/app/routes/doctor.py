from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    AISchedulingRecommendation,
    Appointment,
    AppointmentHistory,
    Doctor,
    DoctorAvailability,
    DoctorPrivateNote,
    Patient,
    PatientNote,
    User,
)
from app.schemas import (
    DoctorAppointmentAction,
    DoctorAuthResponse,
    DoctorAvailabilityIn,
    DoctorLoginRequest,
    DoctorProfileUpdate,
    DoctorPublic,
    DoctorRegisterRequest,
)
from app.security import create_doctor_access_token, get_current_doctor, hash_password, verify_password

router = APIRouter(prefix="/api/doctor", tags=["Doctor Portal"])


def doctor_public(doctor: Doctor) -> DoctorPublic:
    return DoctorPublic(
        doctor_id=doctor.id,
        full_name=doctor.name,
        email=doctor.email,
        specialization=doctor.specialization,
        phone_number=doctor.phone_number,
        license_number=doctor.license_number,
        hospital_or_clinic_name=doctor.location,
        profile_image=doctor.profile_image,
        status=doctor.status,
        consultation_fee=doctor.consultation_fee,
        languages=doctor.languages,
        experience_years=doctor.experience_years,
        about_doctor=doctor.about_doctor,
        consultation_modes=doctor.consultation_modes,
    )


def appointment_payload(db: Session, appointment: Appointment) -> dict:
    patient_user = db.get(User, appointment.user_id)
    patient = db.query(Patient).filter(Patient.user_id == appointment.user_id).first()
    patient_note = db.query(PatientNote).filter(PatientNote.appointment_id == appointment.id).order_by(PatientNote.created_at.desc()).first()
    ai_note = db.query(AISchedulingRecommendation).filter(AISchedulingRecommendation.appointment_id == appointment.id).order_by(AISchedulingRecommendation.created_at.desc()).first()
    private_note = db.query(DoctorPrivateNote).filter(DoctorPrivateNote.appointment_id == appointment.id).order_by(DoctorPrivateNote.created_at.desc()).first()
    return {
        "id": appointment.id,
        "patient_name": patient_user.name if patient_user else "Patient",
        "patient_email": patient_user.email if patient_user else "",
        "patient_age": patient.age if patient else 0,
        "patient_gender": "",
        "reason_for_visit": appointment.specialization,
        "symptoms": patient_note.symptoms if patient_note else "",
        "appointment_time": appointment.starts_at,
        "ends_at": appointment.ends_at,
        "status": appointment.status,
        "urgency_level": appointment.urgency_level,
        "patient_note": patient_note.note_text if patient_note else "",
        "voice_transcription": patient_note.voice_transcription if patient_note else "",
        "ai_recommendation": ai_note.recommendation_text if ai_note else appointment.reasoning,
        "suggested_best_time_slot": ai_note.suggested_slot if ai_note else appointment.starts_at.strftime("%I:%M %p"),
        "ai_reason": ai_note.reason if ai_note else appointment.reasoning,
        "doctor_private_note": private_note.note_text if private_note else "",
    }


def get_owned_appointment(db: Session, doctor: Doctor, appointment_id: int) -> Appointment:
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id, Appointment.doctor_id == doctor.id).first()
    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found for this doctor.")
    return appointment


@router.post("/register", response_model=DoctorAuthResponse, status_code=status.HTTP_201_CREATED)
def register_doctor(payload: DoctorRegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(Doctor).filter(Doctor.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="A doctor account with this email already exists.")
    doctor = Doctor(
        id=f"DOC-{uuid4().hex[:10].upper()}",
        name=payload.full_name.strip(),
        email=payload.email,
        password_hash=hash_password(payload.password),
        specialization=payload.specialization,
        location=payload.hospital_or_clinic_name,
        gender="",
        languages="English",
        phone_number=payload.phone_number,
        license_number=payload.license_number,
        status="active",
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return {"access_token": create_doctor_access_token(doctor), "doctor": doctor_public(doctor)}


@router.post("/login", response_model=DoctorAuthResponse)
def login_doctor(payload: DoctorLoginRequest, db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.email == payload.email).first()
    if doctor is None or not doctor.password_hash or not verify_password(payload.password, doctor.password_hash):
        raise HTTPException(status_code=401, detail="Invalid doctor email or password.")
    if doctor.status != "active":
        raise HTTPException(status_code=403, detail="Doctor account is inactive.")
    return {"access_token": create_doctor_access_token(doctor), "doctor": doctor_public(doctor)}


@router.get("/me", response_model=DoctorPublic)
def me(doctor: Doctor = Depends(get_current_doctor)):
    return doctor_public(doctor)


@router.get("/dashboard")
def dashboard(doctor: Doctor = Depends(get_current_doctor), db: Session = Depends(get_db)):
    now = datetime.now().replace(second=0, microsecond=0)
    today_start = now.replace(hour=0, minute=0)
    today_end = today_start + timedelta(days=1)
    appointments = db.query(Appointment).filter(Appointment.doctor_id == doctor.id).order_by(Appointment.starts_at.asc()).all()
    today = [item for item in appointments if today_start <= item.starts_at < today_end]
    upcoming = [item for item in appointments if item.starts_at >= now and item.status in {"accepted", "confirmed", "pending", "rescheduled"}]
    pending = [item for item in appointments if item.status == "pending"]
    completed = [item for item in appointments if item.status == "completed"]
    cancelled = [item for item in appointments if item.status == "cancelled"]
    next_appointment = upcoming[0] if upcoming else None
    notes = db.query(PatientNote).filter(PatientNote.doctor_id == doctor.id).order_by(PatientNote.created_at.desc()).limit(6).all()
    ai_notes = db.query(AISchedulingRecommendation).filter(AISchedulingRecommendation.doctor_id == doctor.id).order_by(AISchedulingRecommendation.created_at.desc()).limit(6).all()
    return {
        "doctor": doctor_public(doctor),
        "cards": {
            "total_appointments_today": len(today),
            "pending_requests": len(pending),
            "completed_consultations": len(completed),
            "cancelled_appointments": len(cancelled),
            "average_consultation_duration": f"{doctor.appointment_duration_minutes or 30} min",
            "next_appointment_time": next_appointment.starts_at.isoformat() if next_appointment else "",
        },
        "today_appointments": [appointment_payload(db, item) for item in today],
        "upcoming_appointments": [appointment_payload(db, item) for item in upcoming[:8]],
        "pending_requests": [appointment_payload(db, item) for item in pending[:8]],
        "completed_appointments": [appointment_payload(db, item) for item in completed[:8]],
        "patient_notes": [{"id": note.id, "note_text": note.note_text, "symptoms": note.symptoms, "urgency_level": note.urgency_level, "voice_transcription": note.voice_transcription} for note in notes],
        "ai_scheduling_suggestions": [{"id": note.id, "preferred_time": note.preferred_time, "suggested_slot": note.suggested_slot, "recommendation_text": note.recommendation_text, "reason": note.reason, "confidence_score": note.confidence_score} for note in ai_notes],
        "availability_status": "Available" if doctor.status == "active" else "Inactive",
    }


@router.get("/appointments")
def list_appointments(
    search: str = "",
    status_filter: str = "",
    date: str = "",
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    query = db.query(Appointment).join(User, User.id == Appointment.user_id).filter(Appointment.doctor_id == doctor.id)
    if search:
        query = query.filter(User.name.ilike(f"%{search}%"))
    if status_filter:
        query = query.filter(Appointment.status == status_filter)
    if date:
        selected = datetime.fromisoformat(date)
        query = query.filter(Appointment.starts_at >= selected, Appointment.starts_at < selected + timedelta(days=1))
    items = query.order_by(Appointment.starts_at.asc()).all()
    return [appointment_payload(db, item) for item in items]


@router.patch("/appointments/{appointment_id}/accept")
def accept_appointment(appointment_id: int, doctor: Doctor = Depends(get_current_doctor), db: Session = Depends(get_db)):
    appointment = get_owned_appointment(db, doctor, appointment_id)
    appointment.status = "accepted"
    db.add(AppointmentHistory(appointment_id=appointment.id, user_id=appointment.user_id, action="doctor_accepted", details="Doctor accepted appointment request."))
    db.commit()
    return appointment_payload(db, appointment)


@router.patch("/appointments/{appointment_id}/reject")
def reject_appointment(appointment_id: int, payload: DoctorAppointmentAction, doctor: Doctor = Depends(get_current_doctor), db: Session = Depends(get_db)):
    appointment = get_owned_appointment(db, doctor, appointment_id)
    appointment.status = "rejected"
    db.add(AppointmentHistory(appointment_id=appointment.id, user_id=appointment.user_id, action="doctor_rejected", details=payload.reason))
    db.commit()
    return appointment_payload(db, appointment)


@router.patch("/appointments/{appointment_id}/reschedule")
def reschedule_appointment(appointment_id: int, payload: DoctorAppointmentAction, doctor: Doctor = Depends(get_current_doctor), db: Session = Depends(get_db)):
    appointment = get_owned_appointment(db, doctor, appointment_id)
    if payload.starts_at is None:
        raise HTTPException(status_code=422, detail="starts_at is required to reschedule.")
    appointment.starts_at = payload.starts_at.replace(second=0, microsecond=0)
    appointment.ends_at = appointment.starts_at + timedelta(minutes=payload.duration_minutes)
    appointment.status = "rescheduled"
    db.add(AppointmentHistory(appointment_id=appointment.id, user_id=appointment.user_id, action="doctor_rescheduled", details=payload.reason))
    db.commit()
    return appointment_payload(db, appointment)


@router.patch("/appointments/{appointment_id}/complete")
def complete_appointment(appointment_id: int, payload: DoctorAppointmentAction, doctor: Doctor = Depends(get_current_doctor), db: Session = Depends(get_db)):
    appointment = get_owned_appointment(db, doctor, appointment_id)
    appointment.status = "completed"
    if payload.note_text:
        db.add(DoctorPrivateNote(appointment_id=appointment.id, doctor_id=doctor.id, note_text=payload.note_text))
    db.add(AppointmentHistory(appointment_id=appointment.id, user_id=appointment.user_id, action="doctor_completed", details="Consultation completed."))
    db.commit()
    return appointment_payload(db, appointment)


@router.get("/availability")
def list_availability(doctor: Doctor = Depends(get_current_doctor), db: Session = Depends(get_db)):
    items = db.query(DoctorAvailability).filter(DoctorAvailability.doctor_id == doctor.id).order_by(DoctorAvailability.weekday.asc(), DoctorAvailability.start_time.asc()).all()
    return [{
        "id": item.id,
        "day_of_week": item.weekday,
        "start_time": item.start_time,
        "end_time": item.end_time,
        "slot_duration_minutes": item.slot_duration_minutes,
        "is_available": item.status == "active",
        "max_patients_per_slot": item.max_patients_per_slot,
        "emergency_only": item.time_range == "emergency",
    } for item in items]


@router.post("/availability")
def create_availability(payload: DoctorAvailabilityIn, doctor: Doctor = Depends(get_current_doctor), db: Session = Depends(get_db)):
    item = DoctorAvailability(
        doctor_id=doctor.id,
        weekday=payload.day_of_week,
        start_time=payload.start_time,
        end_time=payload.end_time,
        slot_duration_minutes=payload.slot_duration_minutes,
        max_patients_per_slot=payload.max_patients_per_slot,
        status="active" if payload.is_available else "inactive",
        time_range="emergency" if payload.emergency_only else "",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "status": "created"}


@router.patch("/availability/{availability_id}")
def update_availability(availability_id: int, payload: DoctorAvailabilityIn, doctor: Doctor = Depends(get_current_doctor), db: Session = Depends(get_db)):
    item = db.query(DoctorAvailability).filter(DoctorAvailability.id == availability_id, DoctorAvailability.doctor_id == doctor.id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Availability slot not found.")
    item.weekday = payload.day_of_week
    item.start_time = payload.start_time
    item.end_time = payload.end_time
    item.slot_duration_minutes = payload.slot_duration_minutes
    item.max_patients_per_slot = payload.max_patients_per_slot
    item.status = "active" if payload.is_available else "inactive"
    item.time_range = "emergency" if payload.emergency_only else ""
    db.commit()
    return {"id": item.id, "status": "updated"}


@router.delete("/availability/{availability_id}")
def delete_availability(availability_id: int, doctor: Doctor = Depends(get_current_doctor), db: Session = Depends(get_db)):
    item = db.query(DoctorAvailability).filter(DoctorAvailability.id == availability_id, DoctorAvailability.doctor_id == doctor.id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Availability slot not found.")
    db.delete(item)
    db.commit()
    return {"status": "deleted"}


@router.get("/patient-requests")
def patient_requests(doctor: Doctor = Depends(get_current_doctor), db: Session = Depends(get_db)):
    items = db.query(Appointment).filter(Appointment.doctor_id == doctor.id, Appointment.status == "pending").order_by(Appointment.starts_at.asc()).all()
    return [appointment_payload(db, item) for item in items]


@router.patch("/profile", response_model=DoctorPublic)
def update_profile(payload: DoctorProfileUpdate, doctor: Doctor = Depends(get_current_doctor), db: Session = Depends(get_db)):
    data = payload.model_dump(exclude_unset=True)
    if "full_name" in data:
        doctor.name = data["full_name"] or doctor.name
    if "hospital_or_clinic_name" in data:
        doctor.location = data["hospital_or_clinic_name"] or doctor.location
    for source, target in {
        "specialization": "specialization",
        "phone_number": "phone_number",
        "profile_image": "profile_image",
        "consultation_fee": "consultation_fee",
        "languages": "languages",
        "experience_years": "experience_years",
        "about_doctor": "about_doctor",
        "consultation_modes": "consultation_modes",
    }.items():
        if source in data and data[source] is not None:
            setattr(doctor, target, data[source])
    db.commit()
    db.refresh(doctor)
    return doctor_public(doctor)
