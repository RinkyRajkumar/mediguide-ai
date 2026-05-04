# MediGuide AI

Advanced full-stack AI-powered healthcare assistant for a final-year AI/ML project.

## Stack

- Frontend: React + Vite
- Backend: FastAPI
- Auth: JWT + bcrypt
- Database: SQLAlchemy with PostgreSQL support via `DATABASE_URL`; local development falls back to SQLite
- OCR/AI: Production-ready API shape with modular AI agent, MCP server, and medical skills
- Appointment Scheduling: protected AI agent flow with patient preference learning, real-time schedule retrieval, conflict-free booking, rescheduling, cancellation, and doctor load balancing

## Local URLs

- Frontend: http://127.0.0.1:3000
- Backend API: http://127.0.0.1:8001
- API docs: http://127.0.0.1:8001/docs

## Environment

Copy `backend/.env.example` to `backend/.env` for production secrets.

## Protected Scheduling API

- `GET /api/appointments`
- `POST /api/appointments/recommend`
- `POST /api/appointments/book`
- `PUT /api/appointments/{appointment_id}/reschedule`
- `PUT /api/appointments/{appointment_id}/cancel`
- `GET /api/appointments/history`
- `GET /api/patients/{patient_id}/preferences`
- `PUT /api/patients/{patient_id}/preferences`
- `GET /api/doctors?specialization=General Physician`
- `GET /api/doctors/{doctor_id}/availability`
- `POST /api/ai/schedule-memory`
- `POST /api/ai/schedule-memory/search`

All appointment routes require a JWT bearer token.

### Scheduling Schema

The scheduling module uses relational tables for structured booking data:

- `patients`
- `doctors`
- `departments`
- `clinics`
- `doctor_availability`
- `appointments`
- `patient_preferences`
- `appointment_history`
- `appointment_cancellations`
- `agent_schedule_logs`
- `patient_schedule_memory`

Production should use PostgreSQL via `DATABASE_URL`. Local development falls back to SQLite.

### AI Scheduling Agent

The agent rejects unavailable or conflicting slots, then scores valid slots using:

- Specialization match: `+30`
- Preferred time range match: `+20`
- Preferred location match: `+15`
- Preferred language match: `+10`
- Doctor gender preference match: `+10`
- Previous/preferred doctor match: `+10`
- High urgency earliest-slot boost: up to `+25`
- Avoided day/time penalty: `-20`

Every recommendation run is recorded in `agent_schedule_logs`.

### pgvector Memory Layer

Structured appointment, doctor, availability, and preference data stays in normal PostgreSQL tables. The `patient_schedule_memory` table is an additional AI memory layer for semantic preference memories such as:

- “Patient usually prefers evening appointments”
- “Patient often books Hindi-speaking doctors”
- “Patient prefers Central Clinic”

When PostgreSQL + pgvector is enabled, embeddings are stored in the `embedding` column. The local SQLite fallback stores deterministic embeddings as JSON for development/testing.
