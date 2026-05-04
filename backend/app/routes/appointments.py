from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Appointment, AppointmentHistory, User
from app.schemas import (
    AppointmentBookRequest,
    AppointmentCancelRequest,
    AppointmentHistoryResponse,
    AppointmentOut,
    AppointmentRecommendRequest,
    AppointmentRecommendationResponse,
    AppointmentRescheduleBody,
)
from app.security import get_current_user
from app.services.appointment_service import book_appointment, cancel_appointment, recommend_slots

router = APIRouter(prefix="/api/appointments", tags=["Schedule Appointment"])


def serialize_appointment(item: Appointment) -> AppointmentOut:
    return AppointmentOut(
        id=item.id,
        doctor_id=item.doctor_id,
        doctor_name=item.doctor.name,
        specialization=item.specialization,
        starts_at=item.starts_at,
        ends_at=item.ends_at,
        urgency_level=item.urgency_level,
        status=item.status,
        reasoning=item.reasoning,
    )


@router.get("", response_model=list[AppointmentOut])
def list_appointments(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = (
        db.query(Appointment)
        .filter(Appointment.user_id == current_user.id)
        .order_by(Appointment.starts_at.desc())
        .all()
    )
    return [serialize_appointment(item) for item in items]


@router.post("/recommend", response_model=AppointmentRecommendationResponse)
def recommend_appointments(
    payload: AppointmentRecommendRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = recommend_slots(db, current_user, payload)
    if payload.confirm_booking_after_validation and result["recommended_slots"]:
        selected = result["recommended_slots"][0]
        appointment = book_appointment(
            db,
            current_user,
            AppointmentBookRequest(
                doctor_id=selected["doctor_id"],
                starts_at=selected["starts_at"],
                duration_minutes=payload.duration_minutes,
                urgency_level=payload.urgency_level,
                specialization=payload.specialization,
                reasoning=result["reasoning"],
            ),
        )
        result["appointment_id"] = appointment.id
        result["status"] = "confirmed"
    return result


@router.post("/book", response_model=AppointmentOut)
def book(
    payload: AppointmentBookRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return serialize_appointment(book_appointment(db, current_user, payload))


@router.put("/{appointment_id}/cancel", response_model=AppointmentOut)
@router.post("/{appointment_id}/cancel", response_model=AppointmentOut)
def cancel(
    appointment_id: int,
    payload: AppointmentCancelRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return serialize_appointment(cancel_appointment(db, current_user, appointment_id, payload.reason if payload else ""))


@router.put("/{appointment_id}/reschedule", response_model=AppointmentRecommendationResponse)
def reschedule(
    appointment_id: int,
    payload: AppointmentRescheduleBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(Appointment).filter(Appointment.id == appointment_id, Appointment.user_id == current_user.id).first()
    if existing is None:
        raise HTTPException(status_code=404, detail="Appointment not found.")

    if payload.selected_doctor_id and payload.selected_starts_at:
        appointment = book_appointment(
            db,
            current_user,
            AppointmentBookRequest(
                doctor_id=payload.selected_doctor_id,
                starts_at=payload.selected_starts_at,
                duration_minutes=payload.duration_minutes,
                urgency_level=payload.urgency_level,
                specialization=payload.specialization,
                reasoning="Rescheduled by patient after agent validation.",
            ),
            reschedule_id=appointment_id,
        )
        return {
            "recommended_slots": [],
            "reasoning": "Appointment rescheduled and history preserved.",
            "status": "confirmed",
            "appointment_id": appointment.id,
        }

    return recommend_slots(db, current_user, payload)


@router.get("/history", response_model=list[AppointmentHistoryResponse])
def history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(AppointmentHistory)
        .filter(AppointmentHistory.user_id == current_user.id)
        .order_by(AppointmentHistory.created_at.desc())
        .all()
    )


@router.post("/schedule", response_model=AppointmentRecommendationResponse)
def compatibility_schedule(
    payload: AppointmentRecommendRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return recommend_appointments(payload, current_user, db)
