from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import MedicationCatalog, User
from app.schemas import MedicationCatalogOut
from app.security import get_current_user

router = APIRouter(prefix="/api/medications", tags=["Medication Catalog"])


def serialize_medication(item: MedicationCatalog) -> MedicationCatalogOut:
    return MedicationCatalogOut(
        id=item.id,
        med_code=item.med_code,
        name=item.name,
        generic_name=item.generic_name,
        category=item.category,
        form=item.form,
        default_strength=item.default_strength,
        route=item.route,
        rx_required=item.rx_required.lower() == "true",
        common_uses=item.common_uses,
        patient_note=item.patient_note,
        active=item.active.lower() == "true",
    )


@router.get("/catalog", response_model=list[MedicationCatalogOut])
def list_medication_catalog(
    search: str = Query(default="", max_length=120),
    category: str = Query(default="", max_length=120),
    limit: int = Query(default=60, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(MedicationCatalog).filter(MedicationCatalog.active == "True")
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(or_(
            MedicationCatalog.name.ilike(term),
            MedicationCatalog.generic_name.ilike(term),
            MedicationCatalog.category.ilike(term),
            MedicationCatalog.common_uses.ilike(term),
        ))
    if category:
        query = query.filter(MedicationCatalog.category == category)
    items = query.order_by(MedicationCatalog.name.asc()).limit(limit).all()
    return [serialize_medication(item) for item in items]


@router.get("/catalog/categories", response_model=list[str])
def list_medication_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(MedicationCatalog.category)
        .filter(MedicationCatalog.active == "True", MedicationCatalog.category != "")
        .distinct()
        .order_by(MedicationCatalog.category.asc())
        .all()
    )
    return [row[0] for row in rows]
