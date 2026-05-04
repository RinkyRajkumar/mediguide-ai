from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import ScheduleMemoryCreate, ScheduleMemoryOut, ScheduleMemorySearch
from app.security import get_current_user
from app.services.appointment_service import save_schedule_memory, search_schedule_memory

router = APIRouter(prefix="/api/ai/schedule-memory", tags=["pgvector Schedule Memory"])


@router.post("", response_model=ScheduleMemoryOut)
def create_memory(
    payload: ScheduleMemoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return save_schedule_memory(db, current_user.id, payload.memory_text, payload.memory_type, payload.confidence_score)


@router.post("/search", response_model=list[ScheduleMemoryOut])
def search_memory(
    payload: ScheduleMemorySearch,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return search_schedule_memory(db, current_user.id, payload.query, payload.limit)
