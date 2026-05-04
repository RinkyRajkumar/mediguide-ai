import json
import math
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import settings
from app.models import (
    AgentScheduleLog,
    Appointment,
    AppointmentCancellation,
    AppointmentHistory,
    Clinic,
    Doctor,
    DoctorAvailability,
    Patient,
    PatientPreference,
    PatientScheduleMemory,
    User,
)
from app.schemas import AppointmentBookRequest, AppointmentRecommendRequest
from app.skills.appointment_scoring import score_slot, slot_bucket

ACTIVE_STATUSES = {"confirmed", "rescheduled"}


def deterministic_embedding(text: str, dimensions: int = 384) -> list[float]:
    values = [0.0] * dimensions
    for index, char in enumerate(text.lower()):
        values[index % dimensions] += (ord(char) % 31) / 31
    norm = math.sqrt(sum(value * value for value in values)) or 1
    return [round(value / norm, 6) for value in values]


def embedding_for_db(text: str):
    embedding = deterministic_embedding(text)
    return embedding


def cosine_similarity(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b)) / ((math.sqrt(sum(x * x for x in a)) or 1) * (math.sqrt(sum(y * y for y in b)) or 1))


def get_or_create_patient(db: Session, user: User) -> Patient:
    patient = db.query(Patient).filter(Patient.user_id == user.id).first()
    if patient is None:
        patient = Patient(user_id=user.id, full_name=user.name, age=0, phone="")
        db.add(patient)
        db.flush()
    return patient


def get_or_create_preferences(db: Session, user_id: int) -> PatientPreference:
    preferences = db.query(PatientPreference).filter(PatientPreference.user_id == user_id).first()
    if preferences is None:
        preferences = PatientPreference(user_id=user_id)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
    return preferences


def doctor_query(db: Session, specialization: str = "", location: str = "", language: str = "", gender: str = "any"):
    query = db.query(Doctor).filter(Doctor.status == "active")
    if specialization:
        query = query.filter(Doctor.specialization.ilike(f"%{specialization}%"))
    if location:
        query = query.filter(Doctor.location.ilike(f"%{location}%"))
    if language:
        query = query.filter(Doctor.languages.ilike(f"%{language}%"))
    if gender and gender != "any":
        query = query.filter(Doctor.gender.ilike(gender))
    return query.order_by(Doctor.name.asc())


def parse_clock(value: str) -> tuple[int, int]:
    hour, minute = value.split(":")
    return int(hour), int(minute)


def has_overlap(start: datetime, end: datetime, appointments: list[Appointment]) -> bool:
    return any(item.starts_at < end and item.ends_at > start for item in appointments)


def generate_available_slots(db: Session, doctors: list[Doctor], from_time: datetime, duration_minutes: int, days: int = 14) -> list[dict]:
    if from_time < datetime.now().replace(second=0, microsecond=0):
        raise HTTPException(status_code=422, detail="Cannot book appointments in the past.")

    slots: list[dict] = []
    duration = timedelta(minutes=duration_minutes)
    search_start = from_time.replace(second=0, microsecond=0)
    doctor_ids = [doctor.id for doctor in doctors]
    if not doctor_ids:
        return []

    existing = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id.in_(doctor_ids),
            Appointment.status.in_(ACTIVE_STATUSES),
            Appointment.starts_at < search_start + timedelta(days=days),
            Appointment.ends_at > search_start,
        )
        .all()
    )
    by_doctor: dict[str, list[Appointment]] = {}
    for item in existing:
        by_doctor.setdefault(item.doctor_id, []).append(item)

    for doctor in doctors:
        availability = db.query(DoctorAvailability).filter(
            DoctorAvailability.doctor_id == doctor.id,
            DoctorAvailability.status == "active",
        ).all()
        for offset in range(days):
            date = search_start.date() + timedelta(days=offset)
            for available in availability:
                if date.weekday() != available.weekday:
                    continue
                start_hour, start_minute = parse_clock(available.start_time)
                end_hour, end_minute = parse_clock(available.end_time)
                cursor = datetime.combine(date, datetime.min.time()).replace(hour=start_hour, minute=start_minute)
                end_of_day = datetime.combine(date, datetime.min.time()).replace(hour=end_hour, minute=end_minute)
                if cursor < search_start:
                    cursor = search_start
                    if cursor.minute not in (0, 30):
                        cursor = cursor.replace(minute=30 if cursor.minute < 30 else 0)
                        if cursor.minute == 0:
                            cursor += timedelta(hours=1)

                while cursor + duration <= end_of_day:
                    slot_end = cursor + duration
                    if not has_overlap(cursor, slot_end, by_doctor.get(doctor.id, [])):
                        slots.append({"doctor": doctor, "start": cursor, "end": slot_end})
                    cursor += timedelta(minutes=available.slot_duration_minutes)
    return slots


def patient_has_conflict(db: Session, user_id: int, start: datetime, end: datetime, exclude_appointment_id: int | None = None) -> bool:
    query = db.query(Appointment).filter(
        Appointment.user_id == user_id,
        Appointment.status.in_(ACTIVE_STATUSES),
        Appointment.starts_at < end,
        Appointment.ends_at > start,
    )
    if exclude_appointment_id is not None:
        query = query.filter(Appointment.id != exclude_appointment_id)
    return db.query(query.exists()).scalar()


def doctor_has_conflict(db: Session, doctor_id: str, start: datetime, end: datetime, exclude_appointment_id: int | None = None) -> bool:
    query = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.status.in_(ACTIVE_STATUSES),
        Appointment.starts_at < end,
        Appointment.ends_at > start,
    )
    if exclude_appointment_id is not None:
        query = query.filter(Appointment.id != exclude_appointment_id)
    return db.query(query.exists()).scalar()


def serialize_slot(slot: dict) -> dict:
    doctor = slot["doctor"]
    breakdown = slot.get("score_breakdown", {})
    positive_reasons = [key.replace("_", " ") for key, value in breakdown.items() if value > 0][:4]
    reason = "Recommended because it matches " + ", ".join(positive_reasons) + "." if positive_reasons else "Recommended from validated availability and conflict checks."
    confidence = min(0.98, max(0.45, round(slot.get("score", 0) / 120, 2)))
    return {
        "date": slot["start"].strftime("%Y-%m-%d"),
        "time": slot["start"].strftime("%I:%M %p"),
        "starts_at": slot["start"],
        "ends_at": slot["end"],
        "doctor_id": doctor.id,
        "doctor_name": doctor.name,
        "specialization": doctor.specialization,
        "clinic": doctor.location,
        "language_match": slot.get("language_match", False),
        "score": slot.get("score", 0),
        "confidence_score": confidence,
        "recommendation_reason": reason,
        "score_breakdown": breakdown,
    }


def extract_note_intent(note: str) -> dict:
    text = (note or "").lower()
    intent: dict[str, object] = {}
    if not text.strip():
        return intent

    if any(term in text for term in ["after 5", "after five", "evening", "college", "work hours"]):
        intent["preferred_time_range"] = "evening"
    elif any(term in text for term in ["morning", "before noon", "before 12"]):
        intent["preferred_time_range"] = "morning"
    elif any(term in text for term in ["afternoon", "after lunch"]):
        intent["preferred_time_range"] = "afternoon"

    if "female doctor" in text or "lady doctor" in text:
        intent["doctor_gender"] = "female"
    elif "male doctor" in text:
        intent["doctor_gender"] = "male"

    languages = ["english", "hindi", "tamil", "telugu", "marathi", "bengali", "kannada", "malayalam", "gujarati", "punjabi"]
    for language in languages:
        if language in text:
            intent["language"] = language.title()
            break

    clinic_markers = ["clinic", "hospital", "medical hub", "health center", "care centre", "center"]
    if any(marker in text for marker in clinic_markers):
        words = note.replace(".", " ").replace(",", " ").split()
        for index, word in enumerate(words):
            if word.lower() in {"clinic", "hospital", "hub", "center", "centre"}:
                start = max(0, index - 2)
                intent["location"] = " ".join(words[start:index + 1])
                break

    avoided_days = [day for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"] if f"cannot come {day}" in text or f"avoid {day}" in text or f"not available {day}" in text]
    if avoided_days:
        intent["avoided_days"] = avoided_days

    avoided_times = []
    for bucket in ["morning", "afternoon", "evening"]:
        if f"cannot come {bucket}" in text or f"avoid {bucket}" in text or f"not available {bucket}" in text:
            avoided_times.append(bucket)
    if avoided_times:
        intent["avoided_times"] = avoided_times

    if "dr." in text or "doctor" in text:
        words = note.replace(",", " ").replace(".", ". ").split()
        for index, word in enumerate(words):
            if word.lower().startswith("dr"):
                intent["preferred_doctor"] = " ".join(words[index:index + 3]).replace(" .", ".")
                break

    if any(term in text for term in ["urgent", "severe", "as soon as possible", "asap", "emergency"]):
        intent["urgency_hint"] = "high"
    if any(term in text for term in ["follow up", "follow-up", "review visit"]):
        intent["follow_up"] = True
    if any(term in text for term in ["transport", "travel", "wheelchair", "mobility", "far away", "near"]):
        intent["mobility_constraint"] = True
    return intent


def build_ai_understanding(payload: AppointmentRecommendRequest, preferences: PatientPreference, memories: list[PatientScheduleMemory], note_intent: dict) -> dict:
    return {
        "structured_fields": {
            "specialization": payload.specialization,
            "urgency": payload.urgency_level,
            "preferred_time": payload.preferred_time_range,
            "location": payload.location,
            "language": payload.language,
            "doctor_gender": payload.doctor_gender,
        },
        "patient_note_intent": note_intent,
        "saved_preferences": {
            "preferred_time": preferences.preferred_time_range,
            "preferred_language": preferences.preferred_language,
            "preferred_location": preferences.preferred_clinic_location,
            "preferred_doctor_gender": preferences.preferred_doctor_gender,
        },
        "memory_signals": [memory.memory_text for memory in memories[:3]],
    }


def recommend_slots(db: Session, user: User, payload: AppointmentRecommendRequest) -> dict:
    patient = get_or_create_patient(db, user)
    preferences = get_or_create_preferences(db, user.id)
    from_time = (payload.current_datetime or datetime.now()).replace(second=0, microsecond=0)
    note_intent = extract_note_intent(payload.patient_note)
    doctors = doctor_query(db, payload.specialization, payload.location, payload.language, payload.doctor_gender).all()
    slots = generate_available_slots(db, doctors, from_time, payload.duration_minutes)
    memories = search_schedule_memory(db, patient.id, payload.patient_note or payload.specialization, 3) if payload.patient_note else []
    ai_understanding = build_ai_understanding(payload, preferences, memories, note_intent)
    if not slots:
        decision = {
            "recommended_slots": [],
            "reasoning": "No matching doctor availability found after checking specialization, note intent, doctor filters, and conflicts.",
            "status": "conflict",
            "ai_understanding": ai_understanding,
            "warnings": ["No free slot matched the requested filters. Try a broader location, language, or doctor gender preference."],
        }
        log_agent_decision(db, user.id, payload.model_dump(mode="json"), decision, "conflict")
        return decision

    history = db.query(Appointment).filter(Appointment.user_id == user.id).all()
    cancellation_count = db.query(AppointmentCancellation).filter(AppointmentCancellation.user_id == user.id).count()
    earliest_start = min(slot["start"] for slot in slots)
    request_data = payload.model_dump()
    request_data["note_intent"] = note_intent
    if note_intent.get("urgency_hint") == "high":
        request_data["urgency_level"] = "high"

    scored = [
        score_slot(slot, request_data, preferences, history, cancellation_count, earliest_start)
        for slot in slots
        if not patient_has_conflict(db, user.id, slot["start"], slot["end"])
    ]
    scored.sort(key=lambda item: (-item["score"], item["start"] if payload.urgency_level == "high" else slot_bucket(item["start"])))
    top_slots = scored[:3]
    reasoning = "AI scheduling agent ranked slots using structured fields, saved preferences, appointment history, cancellation behavior, pgvector memory, patient note intent, availability, and conflict checks."
    warnings = []
    if note_intent.get("urgency_hint") == "high" and payload.urgency_level != "high":
        warnings.append("Patient note suggests higher urgency, so earlier slots were prioritized.")
    if note_intent.get("avoided_days") or note_intent.get("avoided_times"):
        warnings.append("Avoided days or times from the patient note were penalized during ranking.")
    decision = {
        "recommended_slots": [serialize_slot(slot) for slot in top_slots],
        "reasoning": reasoning,
        "status": "recommendations" if top_slots else "conflict",
        "ai_understanding": ai_understanding,
        "warnings": warnings,
    }
    if payload.patient_note.strip():
        save_schedule_memory(db, patient.id, f"Scheduling note: {payload.patient_note.strip()}", "patient_note", 0.76)
    log_agent_decision(db, user.id, payload.model_dump(mode="json"), decision, decision["status"])
    return decision


def book_appointment(db: Session, user: User, payload: AppointmentBookRequest, reschedule_id: int | None = None) -> Appointment:
    start = payload.starts_at.replace(second=0, microsecond=0)
    end = start + timedelta(minutes=payload.duration_minutes)
    if start < datetime.now().replace(second=0, microsecond=0):
        raise HTTPException(status_code=422, detail="Cannot book appointments in the past.")
    if patient_has_conflict(db, user.id, start, end, exclude_appointment_id=reschedule_id):
        raise HTTPException(status_code=409, detail="Patient already has an appointment at this time.")
    if doctor_has_conflict(db, payload.doctor_id, start, end, exclude_appointment_id=reschedule_id):
        raise HTTPException(status_code=409, detail="Doctor is no longer available at this time.")

    doctor = db.get(Doctor, payload.doctor_id)
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found.")

    if reschedule_id is not None:
        previous = db.query(Appointment).filter(Appointment.id == reschedule_id, Appointment.user_id == user.id).first()
        if previous is None:
            raise HTTPException(status_code=404, detail="Appointment not found.")
        previous.status = "rescheduled"
        db.add(AppointmentHistory(appointment_id=previous.id, user_id=user.id, action="rescheduled_from", details=f"Moved from {previous.starts_at}"))

    appointment = Appointment(
        user_id=user.id,
        doctor_id=doctor.id,
        specialization=payload.specialization or doctor.specialization,
        starts_at=start,
        ends_at=end,
        urgency_level=payload.urgency_level,
        status="confirmed",
        constraints=json.dumps({"source": "schedule_agent"}),
        reasoning=payload.reasoning,
    )
    db.add(appointment)
    db.flush()
    db.add(AppointmentHistory(appointment_id=appointment.id, user_id=user.id, action="booked", details=payload.reasoning))
    update_preferences_from_booking(db, user.id, doctor, start)
    save_schedule_memory(db, user.id, f"Patient booked {slot_bucket(start)} appointment with {doctor.languages} speaking {doctor.gender} doctor at {doctor.location} for {doctor.specialization}.", "booking_behavior", 0.82)
    db.commit()
    db.refresh(appointment)
    return appointment


def cancel_appointment(db: Session, user: User, appointment_id: int, reason: str) -> Appointment:
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id, Appointment.user_id == user.id).first()
    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found.")
    appointment.status = "cancelled"
    db.add(AppointmentCancellation(appointment_id=appointment.id, user_id=user.id, reason=reason))
    db.add(AppointmentHistory(appointment_id=appointment.id, user_id=user.id, action="cancelled", details=reason))
    db.commit()
    db.refresh(appointment)
    return appointment


def update_preferences_from_booking(db: Session, user_id: int, doctor: Doctor, start: datetime) -> None:
    preferences = get_or_create_preferences(db, user_id)
    preferences.preferred_time_range = slot_bucket(start)
    preferences.preferred_doctor_gender = doctor.gender.lower()
    preferences.preferred_language = doctor.languages.split(",")[0]
    preferences.preferred_clinic_location = doctor.location
    preferences.preferred_specialization = doctor.specialization
    preferences.preferred_doctor_id = doctor.id
    preferences.past_booking_behavior = json.dumps({"last_booking": start.isoformat(), "last_doctor_id": doctor.id})


def log_agent_decision(db: Session, user_id: int, request_payload: dict, decision_payload: dict, status: str) -> None:
    db.add(AgentScheduleLog(
        user_id=user_id,
        request_payload=json.dumps(request_payload, default=str),
        decision_payload=json.dumps(decision_payload, default=str),
        status=status,
    ))
    db.commit()


def save_schedule_memory(db: Session, patient_id: int, memory_text: str, memory_type: str, confidence_score: float) -> PatientScheduleMemory:
    embedding = embedding_for_db(memory_text)
    memory = PatientScheduleMemory(
        patient_id=patient_id,
        memory_text=memory_text,
        embedding=embedding if settings.database_url.startswith("postgresql") else json.dumps(embedding),
        memory_type=memory_type,
        confidence_score=confidence_score,
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return memory


def search_schedule_memory(db: Session, patient_id: int, query: str, limit: int) -> list[PatientScheduleMemory]:
    query_embedding = deterministic_embedding(query)
    memories = db.query(PatientScheduleMemory).filter(PatientScheduleMemory.patient_id == patient_id).all()
    ranked = []
    for memory in memories:
        try:
            embedding = json.loads(memory.embedding)
        except Exception:
            embedding = deterministic_embedding(memory.memory_text)
        ranked.append((cosine_similarity(query_embedding, embedding), memory))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [memory for _, memory in ranked[:limit]]
