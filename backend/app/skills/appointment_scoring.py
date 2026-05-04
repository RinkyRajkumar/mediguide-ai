from datetime import datetime

from app.models import Appointment, Doctor, PatientPreference


TIME_BUCKETS = {
    "morning": range(5, 12),
    "afternoon": range(12, 17),
    "evening": range(17, 21),
}


def slot_bucket(value: datetime) -> str:
    for bucket, hours in TIME_BUCKETS.items():
        if value.hour in hours:
            return bucket
    return "any"


def is_avoided(slot_start: datetime, preferences: PatientPreference | None) -> bool:
    if preferences is None:
        return False
    day_name = slot_start.strftime("%A").lower()
    bucket = slot_bucket(slot_start)
    avoided_days = {item.strip().lower() for item in preferences.avoided_days.split(",") if item.strip()}
    avoided_times = {item.strip().lower() for item in preferences.avoided_times.split(",") if item.strip()}
    return day_name in avoided_days or bucket in avoided_times


def note_avoids_slot(slot_start: datetime, note_intent: dict | None) -> bool:
    if not note_intent:
        return False
    day_name = slot_start.strftime("%A").lower()
    bucket = slot_bucket(slot_start)
    avoided_days = {item.lower() for item in note_intent.get("avoided_days", [])}
    avoided_times = {item.lower() for item in note_intent.get("avoided_times", [])}
    return day_name in avoided_days or bucket in avoided_times


def score_slot(
    slot: dict,
    request: dict,
    preferences: PatientPreference | None,
    appointment_history: list[Appointment],
    cancellation_count: int,
    earliest_start: datetime,
) -> dict:
    doctor: Doctor = slot["doctor"]
    start: datetime = slot["start"]
    score = 0
    breakdown: dict[str, int] = {}

    def add(reason: str, points: int) -> None:
        nonlocal score
        score += points
        breakdown[reason] = points

    add("specialization_match", 30)
    note_intent = request.get("note_intent") or {}

    saved_time_range = preferences.preferred_time_range if preferences else "any"
    requested_range = note_intent.get("preferred_time_range") or request.get("preferred_time_range") or saved_time_range
    if requested_range == "any" or slot_bucket(start) == requested_range:
        add("preferred_time_range_match", 20)
        if note_intent.get("preferred_time_range"):
            add("patient_note_time_match", 8)

    location = (note_intent.get("location") or request.get("location") or (preferences.preferred_clinic_location if preferences else "")).lower()
    if location and location in doctor.location.lower():
        add("preferred_location_match", 15)
        if note_intent.get("location"):
            add("patient_note_location_match", 6)

    language = (note_intent.get("language") or request.get("language") or (preferences.preferred_language if preferences else "")).lower()
    language_match = bool(language and language in doctor.languages.lower())
    if language_match:
        add("doctor_language_match", 10)
        if note_intent.get("language"):
            add("patient_note_language_match", 5)

    gender_pref = (note_intent.get("doctor_gender") or request.get("doctor_gender") or (preferences.preferred_doctor_gender if preferences else "any")).lower()
    if gender_pref == "any" or gender_pref == doctor.gender.lower():
        add("doctor_gender_preference_match", 10)
        if note_intent.get("doctor_gender") and gender_pref != "any":
            add("patient_note_gender_match", 5)

    previous_doctors = {item.doctor_id for item in appointment_history if item.status in {"confirmed", "completed", "rescheduled"}}
    if doctor.id in previous_doctors or (preferences and preferences.preferred_doctor_id == doctor.id):
        add("previous_or_preferred_doctor_match", 10)

    preferred_doctor = (note_intent.get("preferred_doctor") or "").lower()
    if preferred_doctor and preferred_doctor in doctor.name.lower():
        add("patient_note_preferred_doctor_match", 12)

    if request.get("urgency_level") == "high":
        minutes_after_earliest = max(int((start - earliest_start).total_seconds() / 60), 0)
        urgency_points = max(0, 25 - min(minutes_after_earliest // 30, 25))
        add("urgent_appointment_available_soon", urgency_points)
    elif request.get("urgency_level") == "medium":
        add("medium_urgency_balanced_availability", 8)

    if is_avoided(start, preferences):
        add("patient_avoided_time_penalty", -20)

    if note_avoids_slot(start, note_intent):
        add("patient_note_avoided_time_penalty", -25)

    if note_intent.get("mobility_constraint") and location and location in doctor.location.lower():
        add("travel_or_mobility_constraint_match", 6)

    if note_intent.get("follow_up"):
        add("follow_up_context_available", 3)

    if cancellation_count >= 2 and slot_bucket(start) == "morning":
        add("cancellation_history_buffer_preference", 4)

    return {
        **slot,
        "score": score,
        "score_breakdown": breakdown,
        "language_match": language_match,
    }
