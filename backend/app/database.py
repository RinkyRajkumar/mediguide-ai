import csv
import json
import re
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models

    Base.metadata.create_all(bind=engine)
    ensure_sqlite_columns()
    seed_doctors()
    seed_medication_catalog()
    seed_doctor_portal()


def ensure_sqlite_columns() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    additions = {
        "doctors": [
            ("email", "VARCHAR(255) DEFAULT ''"),
            ("password_hash", "VARCHAR(255) DEFAULT ''"),
            ("department_id", "INTEGER"),
            ("clinic_id", "INTEGER"),
            ("status", "VARCHAR(32) DEFAULT 'active'"),
            ("phone_number", "VARCHAR(40) DEFAULT ''"),
            ("license_number", "VARCHAR(80) DEFAULT ''"),
            ("profile_image", "VARCHAR(500) DEFAULT ''"),
            ("about_doctor", "TEXT DEFAULT ''"),
            ("consultation_modes", "VARCHAR(40) DEFAULT 'both'"),
            ("qualification", "VARCHAR(240) DEFAULT ''"),
            ("experience_years", "INTEGER DEFAULT 0"),
            ("consultation_fee", "INTEGER DEFAULT 0"),
            ("rating", "FLOAT DEFAULT 0"),
            ("online_consultation", "VARCHAR(8) DEFAULT 'False'"),
            ("max_daily_appointments", "INTEGER DEFAULT 16"),
            ("preferred_patient_age_group", "VARCHAR(40) DEFAULT 'all'"),
            ("created_at", "DATETIME"),
            ("updated_at", "DATETIME"),
        ],
        "departments": [
            ("external_id", "VARCHAR(64) DEFAULT ''"),
        ],
        "clinics": [
            ("external_id", "VARCHAR(64) DEFAULT ''"),
            ("area", "VARCHAR(120) DEFAULT ''"),
            ("phone", "VARCHAR(40) DEFAULT ''"),
        ],
        "doctor_availability": [
            ("external_id", "VARCHAR(64) DEFAULT ''"),
            ("time_range", "VARCHAR(40) DEFAULT ''"),
            ("max_patients_per_slot", "INTEGER DEFAULT 1"),
        ],
        "appointments": [
            ("updated_at", "DATETIME"),
        ],
        "medication_catalog": [
            ("common_uses", "TEXT DEFAULT ''"),
            ("patient_note", "TEXT DEFAULT ''"),
        ],
    }

    with engine.begin() as conn:
        for table, columns in additions.items():
            existing = {row[1] for row in conn.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()}
            for name, definition in columns:
                if name not in existing:
                    conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")


def seed_doctors() -> None:
    from app.models import Clinic, Department, Doctor, DoctorAvailability

    package_dir = Path(__file__).resolve().parent / "seed_data" / "artificial_doctors_seed_package"
    if package_dir.exists():
        seed_from_artificial_package(package_dir)
        return

    departments = {
        "General Physician": "Primary care, common illness, preventive health, and referrals.",
        "Cardiologist": "Heart, blood pressure, and cardiovascular care.",
        "Dermatologist": "Skin, hair, nail, and allergy-related concerns.",
        "Pediatrician": "Child and adolescent healthcare.",
    }
    clinics = {
        "Central Clinic": ("MG Road", "Bengaluru"),
        "North Wing": ("Hebbal", "Bengaluru"),
        "Heart Care Center": ("Indiranagar", "Bengaluru"),
        "Children's Health Unit": ("Jayanagar", "Bengaluru"),
    }

    doctor_rows = [
        ("D101", "Dr. Meera Iyer", "General Physician", "Central Clinic", "Female", "English,Hindi,Tamil", "0,1,2,3,4,5", "09:00", "17:00"),
        ("D102", "Dr. Arjun Sharma", "General Physician", "North Wing", "Male", "English,Hindi", "0,1,2,3,4,5", "10:00", "19:00"),
        ("D201", "Dr. Kavya Rao", "Cardiologist", "Heart Care Center", "Female", "English,Hindi,Kannada", "0,1,2,3,4", "08:30", "15:30"),
        ("D301", "Dr. Sameer Khan", "Dermatologist", "Central Clinic", "Male", "English,Hindi,Urdu", "1,2,3,4,5", "11:00", "18:00"),
        ("D401", "Dr. Nisha Menon", "Pediatrician", "Children's Health Unit", "Female", "English,Hindi,Malayalam", "0,1,2,3,4,5", "09:30", "16:30"),
    ]

    with SessionLocal() as db:
        department_map = {}
        for name, description in departments.items():
            department = db.query(Department).filter(Department.name == name).first()
            if department is None:
                department = Department(name=name, description=description)
                db.add(department)
                db.flush()
            department_map[name] = department

        clinic_map = {}
        for name, (address, city) in clinics.items():
            clinic = db.query(Clinic).filter(Clinic.name == name).first()
            if clinic is None:
                clinic = Clinic(name=name, address=address, city=city)
                db.add(clinic)
                db.flush()
            clinic_map[name] = clinic

        for doctor_id, name, specialization, location, gender, languages, days, start, end in doctor_rows:
            doctor = Doctor(
                id=doctor_id,
                name=name,
                department_id=department_map[specialization].id,
                clinic_id=clinic_map[location].id,
                specialization=specialization,
                location=location,
                gender=gender,
                languages=languages,
                working_days=days,
                working_start=start,
                working_end=end,
                appointment_duration_minutes=30,
            )
            if db.get(Doctor, doctor.id) is None:
                db.add(doctor)
                db.flush()
            else:
                existing = db.get(Doctor, doctor.id)
                existing.department_id = department_map[specialization].id
                existing.clinic_id = clinic_map[location].id

            doctor_ref = db.get(Doctor, doctor_id)
            if not db.query(DoctorAvailability).filter(DoctorAvailability.doctor_id == doctor_id).first():
                for day in [int(item) for item in days.split(",")]:
                    db.add(DoctorAvailability(
                        doctor_id=doctor_ref.id,
                        weekday=day,
                        start_time=start,
                        end_time=end,
                        slot_duration_minutes=30,
                    ))
        db.commit()


def truthy(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def seed_medication_catalog() -> None:
    from app.models import MedicationCatalog

    seed_file = Path(__file__).resolve().parent / "seed_data" / "medication_catalog_seed_200_with_use_cases.sql"
    if not seed_file.exists():
        return

    raw_sql = seed_file.read_text(encoding="utf-8")
    match = re.search(
        r"INSERT INTO medication_catalog\s*\([^)]+\)\s*VALUES\s*(.*?)\s*ON CONFLICT",
        raw_sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return

    values_block = match.group(1).strip().rstrip(";")
    tuple_texts = split_sql_value_tuples(values_block)

    with SessionLocal() as db:
        for tuple_text in tuple_texts:
            try:
                row = parse_sql_tuple(tuple_text)
            except Exception:
                continue
            (
                med_code,
                name,
                generic_name,
                category,
                form,
                default_strength,
                route,
                rx_required,
                common_uses,
                patient_note,
                active,
            ) = row
            medication = db.query(MedicationCatalog).filter(MedicationCatalog.med_code == med_code).first()
            if medication is None:
                medication = MedicationCatalog(med_code=med_code, name=name)
                db.add(medication)
            medication.name = name or ""
            medication.generic_name = generic_name or ""
            medication.category = category or ""
            medication.form = form or ""
            medication.default_strength = default_strength or ""
            medication.route = route or ""
            medication.rx_required = str(bool(rx_required))
            medication.common_uses = common_uses or ""
            medication.patient_note = patient_note or ""
            medication.active = str(bool(active))
        db.commit()


def seed_doctor_portal() -> None:
    from app.models import AISchedulingRecommendation, Appointment, Doctor, DoctorAvailability, Patient, PatientNote, User
    from app.security import hash_password

    with SessionLocal() as db:
        shared_doctor_hash = hash_password("Doctor@123")
        for indexed_doctor in db.query(Doctor).filter(Doctor.status == "active").all():
            if not indexed_doctor.email:
                slug = re.sub(r"[^a-z0-9]+", "-", indexed_doctor.name.lower().replace("dr.", "dr")).strip("-")
                indexed_doctor.email = f"{slug}-{indexed_doctor.id[:6]}@mediguide.ai"
            if not indexed_doctor.password_hash:
                indexed_doctor.password_hash = shared_doctor_hash
            if not indexed_doctor.license_number:
                indexed_doctor.license_number = f"MED-{indexed_doctor.id[:8].upper()}"
            if not indexed_doctor.phone_number:
                indexed_doctor.phone_number = "+91 90000 11111"

        doctor = db.query(Doctor).filter(Doctor.email == "dentist@mediguide.ai").first()
        if doctor is None:
            doctor = db.get(Doctor, "aad917ce-0f59-4772-9a47-2eedc5961eec")
        if doctor is None:
            doctor = db.query(Doctor).filter(Doctor.specialization == "Dentistry", Doctor.status == "active").order_by(Doctor.rating.desc()).first()
        if doctor is None:
            return

        doctor.email = "dentist@mediguide.ai"
        doctor.password_hash = hash_password("Dentist@123")
        doctor.phone_number = doctor.phone_number or "+91 90000 22222"
        doctor.license_number = doctor.license_number or "DENT-MED-2026-001"
        doctor.about_doctor = doctor.about_doctor or "Dentist using MediGuide AI to manage dental appointments, patient requests, oral health notes, and scheduling workflows."
        doctor.consultation_modes = doctor.consultation_modes or "both"
        doctor.consultation_fee = doctor.consultation_fee or 800
        doctor.experience_years = doctor.experience_years or 23
        doctor.status = "active"

        demo_user = db.query(User).filter(User.email == "patient.demo@mediguide.ai").first()
        if demo_user is None:
            demo_user = User(name="Riya Sharma", email="patient.demo@mediguide.ai", password_hash=hash_password("Patient@123"))
            db.add(demo_user)
            db.flush()
        patient = db.query(Patient).filter(Patient.user_id == demo_user.id).first()
        if patient is None:
            patient = Patient(user_id=demo_user.id, full_name=demo_user.name, age=29, phone="+91 98888 77777", blood_group="O+")
            db.add(patient)
            db.flush()

        now = __import__("datetime").datetime.now().replace(second=0, microsecond=0)
        appointment_specs = [
            ("pending", now.replace(hour=16, minute=30), "medium", "Tooth pain and gum sensitivity"),
            ("accepted", now.replace(hour=18, minute=0), "low", "Follow-up after dental cleaning"),
            ("completed", now.replace(hour=10, minute=30), "low", "Routine dental consultation completed"),
        ]
        for status, starts_at, urgency, symptoms in appointment_specs:
            existing = db.query(Appointment).filter(Appointment.doctor_id == doctor.id, Appointment.user_id == demo_user.id, Appointment.starts_at == starts_at).first()
            if existing is None:
                existing = Appointment(
                    user_id=demo_user.id,
                    doctor_id=doctor.id,
                    specialization=doctor.specialization,
                    starts_at=starts_at,
                    ends_at=starts_at + __import__("datetime").timedelta(minutes=30),
                    urgency_level=urgency,
                    status=status,
                    constraints="{}",
                    reasoning="AI matched patient preference, urgency, and doctor availability.",
                )
                db.add(existing)
                db.flush()
            if not db.query(PatientNote).filter(PatientNote.appointment_id == existing.id).first():
                db.add(PatientNote(
                    appointment_id=existing.id,
                    patient_id=demo_user.id,
                    doctor_id=doctor.id,
                    note_text="Patient prefers evening appointments and requests a quick consultation near the clinic.",
                    voice_transcription="I can come after work around 4:30 PM if possible.",
                    symptoms=symptoms,
                    urgency_level=urgency,
                ))
            if not db.query(AISchedulingRecommendation).filter(AISchedulingRecommendation.appointment_id == existing.id).first():
                db.add(AISchedulingRecommendation(
                    appointment_id=existing.id,
                    doctor_id=doctor.id,
                    patient_id=demo_user.id,
                    preferred_time="Evening",
                    suggested_slot=starts_at.strftime("%I:%M %p"),
                    recommendation_text=f"AI suggests {starts_at.strftime('%I:%M %p')} because it matches patient preference and the doctor has an open slot.",
                    reason="Patient prefers evening appointments and doctor availability has no conflict.",
                    confidence_score=0.86,
                ))

        if not db.query(DoctorAvailability).filter(DoctorAvailability.doctor_id == doctor.id).first():
            for weekday in range(0, 6):
                db.add(DoctorAvailability(
                    doctor_id=doctor.id,
                    weekday=weekday,
                    start_time="09:00",
                    end_time="18:00",
                    slot_duration_minutes=30,
                    max_patients_per_slot=1,
                    status="active",
                ))

        db.commit()


def split_sql_value_tuples(values_block: str) -> list[str]:
    tuples: list[str] = []
    in_string = False
    depth = 0
    start = 0
    index = 0
    while index < len(values_block):
        char = values_block[index]
        if char == "'":
            if in_string and index + 1 < len(values_block) and values_block[index + 1] == "'":
                index += 2
                continue
            in_string = not in_string
        elif not in_string:
            if char == "(":
                if depth == 0:
                    start = index
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    tuples.append(values_block[start:index + 1])
        index += 1
    return tuples


def parse_sql_tuple(tuple_text: str) -> list[object]:
    text = tuple_text.strip()
    if text.startswith("(") and text.endswith(")"):
        text = text[1:-1]
    values: list[object] = []
    current: list[str] = []
    in_string = False
    index = 0
    while index < len(text):
        char = text[index]
        if char == "'":
            if in_string and index + 1 < len(text) and text[index + 1] == "'":
                current.append("'")
                index += 2
                continue
            in_string = not in_string
        elif char == "," and not in_string:
            values.append(coerce_sql_value("".join(current).strip()))
            current = []
        else:
            current.append(char)
        index += 1
    values.append(coerce_sql_value("".join(current).strip()))
    return values


def coerce_sql_value(value: str) -> object:
    upper = value.upper()
    if upper == "TRUE":
        return True
    if upper == "FALSE":
        return False
    if upper == "NULL":
        return None
    return value


def seed_from_artificial_package(package_dir: Path) -> None:
    from app.models import Clinic, Department, Doctor, DoctorAvailability

    clinics_csv = package_dir / "clinics_seed.csv"
    departments_csv = package_dir / "departments_seed.csv"
    doctors_csv = package_dir / "doctors_seed.csv"
    availability_csv = package_dir / "doctor_availability_seed.csv"
    doctors_json = package_dir / "doctors_seed.json"

    expected_counts = {}
    if doctors_json.exists():
        with doctors_json.open("r", encoding="utf-8") as handle:
            json_data = json.load(handle)
            expected_counts = {
                "departments": len(json_data.get("departments", [])),
                "clinics": len(json_data.get("clinics", [])),
                "doctors": len(json_data.get("doctors", [])),
                "availability": len(json_data.get("doctor_availability", [])),
            }

    with SessionLocal() as db:
        department_by_name = {}
        external_department_map = {}
        with departments_csv.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                department = db.query(Department).filter(Department.external_id == row["id"]).first()
                if department is None:
                    department = db.query(Department).filter(Department.name == row["name"]).first()
                if department is None:
                    department = Department(external_id=row["id"], name=row["name"], description=row.get("description", ""))
                    db.add(department)
                    db.flush()
                else:
                    department.external_id = row["id"]
                    department.description = row.get("description", department.description)
                department_by_name[department.name] = department
                external_department_map[row["id"]] = department

        clinic_by_name = {}
        external_clinic_map = {}
        with clinics_csv.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                clinic = db.query(Clinic).filter(Clinic.external_id == row["id"]).first()
                if clinic is None:
                    clinic = db.query(Clinic).filter(Clinic.name == row["name"]).first()
                if clinic is None:
                    clinic = Clinic(
                        external_id=row["id"],
                        name=row["name"],
                        city=row.get("city", ""),
                        area=row.get("area", ""),
                        address=row.get("address", ""),
                        phone=row.get("phone", ""),
                    )
                    db.add(clinic)
                    db.flush()
                else:
                    clinic.external_id = row["id"]
                    clinic.city = row.get("city", clinic.city)
                    clinic.area = row.get("area", clinic.area)
                    clinic.address = row.get("address", clinic.address)
                    clinic.phone = row.get("phone", clinic.phone)
                clinic_by_name[clinic.name] = clinic
                external_clinic_map[row["id"]] = clinic

        with doctors_csv.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                department = department_by_name.get(row["department"])
                clinic = clinic_by_name.get(row["clinic"])
                if department is None or clinic is None:
                    continue
                doctor = db.get(Doctor, row["id"])
                if doctor is None:
                    doctor = Doctor(id=row["id"], name=row["full_name"])
                    db.add(doctor)
                doctor.name = row["full_name"]
                doctor.department_id = department.id
                doctor.clinic_id = clinic.id
                doctor.specialization = row["department"]
                doctor.location = row["clinic"]
                doctor.gender = row["gender"]
                doctor.languages = row["languages"].replace("|", ",")
                doctor.working_days = doctor.working_days or "0,1,2,3,4"
                doctor.working_start = doctor.working_start or "09:00"
                doctor.working_end = doctor.working_end or "17:00"
                doctor.qualification = row.get("qualification", "")
                doctor.experience_years = int(row.get("experience_years") or 0)
                doctor.consultation_fee = int(row.get("consultation_fee") or 0)
                doctor.rating = float(row.get("rating") or 0)
                doctor.online_consultation = str(truthy(row.get("online_consultation", "")))
                doctor.max_daily_appointments = int(row.get("max_daily_appointments") or 16)
                doctor.preferred_patient_age_group = row.get("preferred_patient_age_group", "all")
                doctor.status = "active" if truthy(row.get("is_active", "True")) else "inactive"

        with availability_csv.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                if db.query(DoctorAvailability).filter(DoctorAvailability.external_id == row["id"]).first():
                    continue
                if db.get(Doctor, row["doctor_id"]) is None:
                    continue
                availability = DoctorAvailability(
                    external_id=row["id"],
                    doctor_id=row["doctor_id"],
                    weekday=int(row["day_of_week"]),
                    start_time=row["start_time"],
                    end_time=row["end_time"],
                    time_range=row.get("time_range", ""),
                    slot_duration_minutes=int(row.get("slot_duration_minutes") or 30),
                    max_patients_per_slot=int(row.get("max_patients_per_slot") or 1),
                    status="active" if truthy(row.get("is_active", "True")) else "inactive",
                )
                db.add(availability)

        db.commit()

        if expected_counts:
            actual_counts = {
                "departments": db.query(Department).count(),
                "clinics": db.query(Clinic).count(),
                "doctors": db.query(Doctor).count(),
                "availability": db.query(DoctorAvailability).count(),
            }
            db.info["seed_counts"] = {"expected": expected_counts, "actual": actual_counts}
