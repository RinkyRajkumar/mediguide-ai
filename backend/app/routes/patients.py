import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PatientPreference, User
from app.schemas import PatientPreferenceIn, PatientPreferenceOut
from app.security import get_current_user
from app.services.appointment_service import get_or_create_preferences

router = APIRouter(prefix="/api/patients", tags=["Patient Scheduling Preferences"])


def ensure_self(patient_id: int, current_user: User) -> None:
    if patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only access your own preferences.")


def serialize_preferences(preferences: PatientPreference) -> PatientPreferenceOut:
    try:
        behavior = json.loads(preferences.past_booking_behavior or "{}")
    except Exception:
        behavior = {}
    return PatientPreferenceOut(
        patient_id=preferences.user_id,
        preferred_time_range=preferences.preferred_time_range,
        preferred_doctor_gender=preferences.preferred_doctor_gender,
        preferred_language=preferences.preferred_language,
        preferred_clinic_location=preferences.preferred_clinic_location,
        preferred_specialization=preferences.preferred_specialization,
        preferred_doctor_id=preferences.preferred_doctor_id,
        avoided_days=preferences.avoided_days,
        avoided_times=preferences.avoided_times,
        past_booking_behavior=behavior,
    )


@router.get("/{patient_id}/preferences", response_model=PatientPreferenceOut)
def get_preferences(patient_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_self(patient_id, current_user)
    return serialize_preferences(get_or_create_preferences(db, current_user.id))


@router.put("/{patient_id}/preferences", response_model=PatientPreferenceOut)
def update_preferences(
    patient_id: int,
    payload: PatientPreferenceIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_self(patient_id, current_user)
    preferences = get_or_create_preferences(db, current_user.id)
    for key, value in payload.model_dump().items():
        setattr(preferences, key, value)
    db.commit()
    db.refresh(preferences)
    return serialize_preferences(preferences)


@router.get("/{patient_id}/appointment-history")
def appointment_history(patient_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_self(patient_id, current_user)
    from app.routes.appointments import history

    return history(current_user, db)
