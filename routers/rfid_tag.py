# routes/rfid_tag.py
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from typing import List, Optional

from models.rfid_tag import RFIDTag
from database.session import get_session

router = APIRouter(prefix="/rfid-tags", tags=["RFID Tags"])

# -------------------------------
# Liste tags
# GET /rfid-tags
# -------------------------------
@router.get("/")
def get_rfid_tags(session: Session = Depends(get_session)):
    try:
        tags = session.exec(select(RFIDTag)).all()
        return {"status": 200, "data": tags}
    except Exception:
        return {"status": 400, "data": []}

# -------------------------------
# Détail tag
# GET /rfid-tags/{tag_id}
# -------------------------------
@router.get("/{tag_id}")
def get_rfid_tag(tag_id: int, session: Session = Depends(get_session)):
    try:
        tag = session.get(RFIDTag, tag_id)
        if not tag:
            return {"status": 400, "data": []}
        return {"status": 200, "data": tag}
    except Exception:
        return {"status": 400, "data": []}

# -------------------------------
# Créer tag
# POST /rfid-tags
# -------------------------------
@router.post("/")
def create_rfid_tag(tag: RFIDTag, session: Session = Depends(get_session)):
    try:
        session.add(tag)
        session.commit()
        session.refresh(tag)
        return {"status": 200, "data": tag}
    except Exception:
        session.rollback()
        return {"status": 400, "data": []}

# -------------------------------
# Modifier tag
# PUT /rfid-tags/{tag_id}
# -------------------------------
@router.put("/{tag_id}")
def update_rfid_tag(tag_id: int, tag_data: RFIDTag, session: Session = Depends(get_session)):
    try:
        tag = session.get(RFIDTag, tag_id)
        if not tag:
            return {"status": 400, "data": []}
        tag.code_rfid = tag_data.code_rfid
        tag.employee_id = tag_data.employee_id
        tag.machine_id = tag_data.machine_id
        session.add(tag)
        session.commit()
        session.refresh(tag)
        return {"status": 200, "data": tag}
    except Exception:
        session.rollback()
        return {"status": 400, "data": []}

# -------------------------------
# Supprimer tag
# DELETE /rfid-tags/{tag_id}
# -------------------------------
@router.delete("/{tag_id}")
def delete_rfid_tag(tag_id: int, session: Session = Depends(get_session)):
    try:
        tag = session.get(RFIDTag, tag_id)
        if not tag:
            return {"status": 400, "data": []}
        session.delete(tag)
        session.commit()
        return {"status": 200, "data": {"message": "Tag deleted successfully"}}
    except Exception:
        session.rollback()
        return {"status": 400, "data": []}
