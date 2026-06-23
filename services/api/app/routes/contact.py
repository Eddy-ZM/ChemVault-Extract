from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ContactMessage
from app.schemas import ContactMessageCreateRequest, ContactMessageRead

router = APIRouter(prefix="/contact", tags=["contact"])


@router.post("", response_model=ContactMessageRead, status_code=status.HTTP_201_CREATED)
def create_contact_message(
    payload: ContactMessageCreateRequest,
    db: Session = Depends(get_db),
) -> ContactMessageRead:
    name = payload.name.strip()
    email = payload.email.strip().lower()
    message = payload.message.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required.")
    if "@" not in email:
        raise HTTPException(status_code=400, detail="A valid email is required.")
    if not message:
        raise HTTPException(status_code=400, detail="Message is required.")

    contact_message = ContactMessage(
        name=name,
        email=email,
        role=payload.role.strip() if payload.role else None,
        organization=payload.organization.strip() if payload.organization else None,
        message=message,
    )
    db.add(contact_message)
    db.commit()
    db.refresh(contact_message)
    return ContactMessageRead.model_validate(contact_message)
