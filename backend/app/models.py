from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import settings
from app.database import Base

try:
    from pgvector.sqlalchemy import Vector
except Exception:
    Vector = None


EmbeddingColumn = Vector(384) if Vector is not None and settings.database_url.startswith("postgresql") else Text


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    history: Mapped[list["HealthHistory"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    patient: Mapped["Patient"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    blood_group: Mapped[str] = mapped_column(String(8), nullable=False, default="")
    age: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped[User] = relationship(back_populates="patient")


class HealthHistory(Base):
    __tablename__ = "health_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(40), nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="history")


class MedicationCatalog(Base):
    __tablename__ = "medication_catalog"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    med_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    generic_name: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    category: Mapped[str] = mapped_column(String(120), nullable=False, default="", index=True)
    form: Mapped[str] = mapped_column(String(60), nullable=False, default="")
    default_strength: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    route: Mapped[str] = mapped_column(String(60), nullable=False, default="")
    rx_required: Mapped[str] = mapped_column(String(8), nullable=False, default="True")
    common_uses: Mapped[str] = mapped_column(Text, nullable=False, default="")
    patient_note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    active: Mapped[str] = mapped_column(String(8), nullable=False, default="True", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True, index=True)
    clinic_id: Mapped[int | None] = mapped_column(ForeignKey("clinics.id"), nullable=True, index=True)
    specialization: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(120), nullable=False)
    gender: Mapped[str] = mapped_column(String(40), nullable=False)
    languages: Mapped[str] = mapped_column(String(255), nullable=False)
    working_days: Mapped[str] = mapped_column(String(80), nullable=False, default="0,1,2,3,4")
    working_start: Mapped[str] = mapped_column(String(5), nullable=False, default="09:00")
    working_end: Mapped[str] = mapped_column(String(5), nullable=False, default="17:00")
    appointment_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    qualification: Mapped[str] = mapped_column(String(240), nullable=False, default="")
    experience_years: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    consultation_fee: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rating: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    online_consultation: Mapped[str] = mapped_column(String(8), nullable=False, default="False")
    max_daily_appointments: Mapped[int] = mapped_column(Integer, nullable=False, default=16)
    preferred_patient_age_group: Mapped[str] = mapped_column(String(40), nullable=False, default="all")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    appointments: Mapped[list["Appointment"]] = relationship(back_populates="doctor")
    department: Mapped["Department"] = relationship(back_populates="doctors")
    clinic: Mapped["Clinic"] = relationship(back_populates="doctors")
    availability_slots: Mapped[list["DoctorAvailability"]] = relationship(back_populates="doctor", cascade="all, delete-orphan")


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    external_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    doctors: Mapped[list[Doctor]] = relationship(back_populates="department")


class Clinic(Base):
    __tablename__ = "clinics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    external_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    city: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    area: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    phone: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    doctors: Mapped[list[Doctor]] = relationship(back_populates="clinic")


class DoctorAvailability(Base):
    __tablename__ = "doctor_availability"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    external_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    doctor_id: Mapped[str] = mapped_column(ForeignKey("doctors.id"), nullable=False, index=True)
    weekday: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    start_time: Mapped[str] = mapped_column(String(5), nullable=False)
    end_time: Mapped[str] = mapped_column(String(5), nullable=False)
    time_range: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    slot_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    max_patients_per_slot: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    doctor: Mapped[Doctor] = relationship(back_populates="availability_slots")


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    doctor_id: Mapped[str] = mapped_column(ForeignKey("doctors.id"), nullable=False, index=True)
    specialization: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False, index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False, index=True)
    urgency_level: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="confirmed")
    constraints: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    reasoning: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped[User] = relationship(back_populates="appointments")
    doctor: Mapped[Doctor] = relationship(back_populates="appointments")

    __table_args__ = (
        UniqueConstraint("doctor_id", "starts_at", "status", name="uq_doctor_start_status"),
    )


class PatientPreference(Base):
    __tablename__ = "patient_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False, index=True)
    preferred_time_range: Mapped[str] = mapped_column(String(40), nullable=False, default="morning")
    preferred_doctor_gender: Mapped[str] = mapped_column(String(40), nullable=False, default="any")
    preferred_language: Mapped[str] = mapped_column(String(80), nullable=False, default="English")
    preferred_clinic_location: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    preferred_specialization: Mapped[str] = mapped_column(String(120), nullable=False, default="General Medicine")
    preferred_doctor_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    avoided_days: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    avoided_times: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    past_booking_behavior: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AppointmentHistory(Base):
    __tablename__ = "appointment_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AppointmentCancellation(Base):
    __tablename__ = "appointment_cancellations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AgentScheduleLog(Base):
    __tablename__ = "agent_schedule_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    request_payload: Mapped[str] = mapped_column(Text, nullable=False)
    decision_payload: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="success")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PatientScheduleMemory(Base):
    __tablename__ = "patient_schedule_memory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    memory_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[object] = mapped_column(EmbeddingColumn, nullable=True)
    memory_type: Mapped[str] = mapped_column(String(80), nullable=False, default="preference")
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.75)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
