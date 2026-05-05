from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class UserPublic(BaseModel):
    id: int
    name: str
    email: str

    model_config = {"from_attributes": True}


class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        email = value.strip().lower()
        if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
            raise ValueError("Enter a valid email address.")
        return email


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return value.strip().lower()


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class DoctorLoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return value.strip().lower()


class DoctorRegisterRequest(DoctorLoginRequest):
    full_name: str = Field(min_length=2, max_length=120)
    specialization: str = Field(min_length=2, max_length=120)
    phone_number: str = Field(default="", max_length=40)
    license_number: str = Field(min_length=3, max_length=80)
    hospital_or_clinic_name: str = Field(default="", max_length=120)


class DoctorPublic(BaseModel):
    doctor_id: str
    full_name: str
    email: str
    specialization: str
    phone_number: str
    license_number: str
    hospital_or_clinic_name: str
    profile_image: str
    status: str
    consultation_fee: int
    languages: str
    experience_years: int
    about_doctor: str
    consultation_modes: str


class DoctorAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    doctor: DoctorPublic


class DoctorProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    specialization: str | None = Field(default=None, max_length=120)
    phone_number: str | None = Field(default=None, max_length=40)
    hospital_or_clinic_name: str | None = Field(default=None, max_length=120)
    profile_image: str | None = Field(default=None, max_length=500)
    consultation_fee: int | None = Field(default=None, ge=0, le=100000)
    languages: str | None = Field(default=None, max_length=255)
    experience_years: int | None = Field(default=None, ge=0, le=80)
    about_doctor: str | None = Field(default=None, max_length=2000)
    consultation_modes: str | None = Field(default=None, max_length=40)


class DoctorAvailabilityIn(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    start_time: str = Field(min_length=4, max_length=5)
    end_time: str = Field(min_length=4, max_length=5)
    slot_duration_minutes: int = Field(default=30, ge=5, le=240)
    is_available: bool = True
    max_patients_per_slot: int = Field(default=1, ge=1, le=20)
    emergency_only: bool = False


class DoctorAppointmentAction(BaseModel):
    reason: str = Field(default="", max_length=600)
    note_text: str = Field(default="", max_length=2000)
    starts_at: datetime | None = None
    duration_minutes: int = Field(default=30, ge=15, le=180)


class SymptomRequest(BaseModel):
    symptoms: list[str] = Field(min_length=1)
    age: int | None = Field(default=None, ge=0, le=120)
    gender: str | None = None
    duration_days: int | None = Field(default=None, ge=0, le=365)
    severity: int | None = Field(default=None, ge=1, le=10)
    language: str = "English"


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    language: str = "English"


class DiseasePredictionRequest(BaseModel):
    symptoms: list[str] = Field(min_length=1)
    age: int | None = Field(default=None, ge=0, le=120)
    duration_days: int | None = Field(default=None, ge=0, le=365)


class RiskRequest(BaseModel):
    symptoms: list[str] = Field(default_factory=list)
    severity: int = Field(ge=1, le=10)
    duration_days: int = Field(ge=0, le=365)
    age: int | None = Field(default=None, ge=0, le=120)


class HealthHistoryCreate(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    category: str = Field(min_length=2, max_length=80)
    risk_level: Literal["Low", "Medium", "High", "Emergency"]
    risk_score: int = Field(ge=0, le=100)
    summary: str = Field(min_length=2, max_length=4000)


class HealthHistoryOut(HealthHistoryCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class MedicationCatalogOut(BaseModel):
    id: int
    med_code: str
    name: str
    generic_name: str
    category: str
    form: str
    default_strength: str
    route: str
    rx_required: bool
    common_uses: str
    patient_note: str
    active: bool


class AppointmentConstraints(BaseModel):
    location: str | None = Field(default=None, max_length=120)
    gender_preference: str | None = Field(default=None, max_length=40)
    language: str | None = Field(default=None, max_length=80)


class AppointmentScheduleRequest(BaseModel):
    patient_id: int | None = None
    preferred_time_ranges: list[str] = Field(default_factory=list)
    urgency_level: Literal["low", "medium", "high"]
    doctor_specialization_required: str = Field(min_length=2, max_length=120)
    current_datetime: datetime | None = None
    constraints: AppointmentConstraints = Field(default_factory=AppointmentConstraints)
    appointment_duration_minutes: int = Field(default=30, ge=15, le=120)
    confirm_booking: bool = True


class AppointmentRescheduleRequest(AppointmentScheduleRequest):
    appointment_id: int


class AppointmentSlot(BaseModel):
    date: str
    time: str
    doctor_id: str
    doctor_name: str | None = None
    specialization: str | None = None


class AppointmentScheduleResponse(BaseModel):
    recommended_slot: AppointmentSlot | None
    alternative_slots: list[AppointmentSlot]
    reasoning: str
    urgency_handling: str
    status: Literal["confirmed", "suggestion", "conflict"]
    appointment_id: int | None = None
    preference_profile: dict = Field(default_factory=dict)


class AppointmentOut(BaseModel):
    id: int
    doctor_id: str
    doctor_name: str
    specialization: str
    starts_at: datetime
    ends_at: datetime
    urgency_level: str
    status: str
    reasoning: str

    model_config = {"from_attributes": True}


class PatientPreferenceIn(BaseModel):
    preferred_time_range: Literal["morning", "afternoon", "evening", "any"] = "morning"
    preferred_doctor_gender: Literal["male", "female", "any"] = "any"
    preferred_language: str = Field(default="English", max_length=80)
    preferred_clinic_location: str = Field(default="", max_length=120)
    preferred_specialization: str = Field(default="General Medicine", max_length=120)
    preferred_doctor_id: str = Field(default="", max_length=24)
    avoided_days: str = Field(default="", max_length=120)
    avoided_times: str = Field(default="", max_length=120)


class PatientPreferenceOut(PatientPreferenceIn):
    patient_id: int
    past_booking_behavior: dict = Field(default_factory=dict)


class AppointmentRecommendRequest(BaseModel):
    specialization: str = Field(min_length=2, max_length=120)
    urgency_level: Literal["low", "medium", "high"]
    preferred_time_range: Literal["morning", "afternoon", "evening", "any"] = "any"
    current_datetime: datetime | None = None
    duration_minutes: int = Field(default=30, ge=15, le=120)
    location: str = Field(default="", max_length=120)
    doctor_gender: Literal["male", "female", "any"] = "any"
    language: str = Field(default="", max_length=80)
    confirm_booking_after_validation: bool = False
    patient_note: str = Field(default="", max_length=2000)


class RecommendedSlot(BaseModel):
    date: str
    time: str
    starts_at: datetime
    ends_at: datetime
    doctor_id: str
    doctor_name: str
    specialization: str
    clinic: str
    language_match: bool
    score: int
    confidence_score: float
    recommendation_reason: str
    score_breakdown: dict


class AppointmentRecommendationResponse(BaseModel):
    recommended_slots: list[RecommendedSlot]
    reasoning: str
    status: Literal["recommendations", "confirmed", "conflict"]
    appointment_id: int | None = None
    ai_understanding: dict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class AppointmentBookRequest(BaseModel):
    doctor_id: str
    starts_at: datetime
    duration_minutes: int = Field(default=30, ge=15, le=120)
    urgency_level: Literal["low", "medium", "high"]
    specialization: str = Field(min_length=2, max_length=120)
    reasoning: str = ""
    patient_note: str = Field(default="", max_length=2000)
    voice_transcription: str = Field(default="", max_length=2000)
    preferred_time_range: str = Field(default="", max_length=80)
    recommendation_reason: str = Field(default="", max_length=1000)


class AppointmentCancelRequest(BaseModel):
    reason: str = Field(default="", max_length=500)


class AppointmentRescheduleBody(AppointmentRecommendRequest):
    selected_starts_at: datetime | None = None
    selected_doctor_id: str | None = None


class AppointmentHistoryResponse(BaseModel):
    id: int
    appointment_id: int
    action: str
    details: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ScheduleMemoryCreate(BaseModel):
    memory_text: str = Field(min_length=5, max_length=1000)
    memory_type: str = Field(default="preference", max_length=80)
    confidence_score: float = Field(default=0.75, ge=0, le=1)


class ScheduleMemorySearch(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    limit: int = Field(default=5, ge=1, le=20)


class ScheduleMemoryOut(BaseModel):
    id: int
    patient_id: int
    memory_text: str
    memory_type: str
    confidence_score: float
    created_at: datetime

    model_config = {"from_attributes": True}
