from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Invoice, User
from app.schemas import InvoiceCreate, InvoiceOut
from app.security import get_current_user, require_roles
from app.services.billing import create_invoice

router = APIRouter(prefix="/api/v1", tags=["billing"])


@router.post("/invoices", response_model=InvoiceOut, status_code=201, dependencies=[Depends(require_roles("admin"))])
def issue_invoice(payload: InvoiceCreate, db: Session = Depends(get_db)):
    return create_invoice(db, payload.usage_record_id)


@router.get("/invoices", response_model=list[InvoiceOut])
def list_invoices(student_id: str | None = None, course_id: str | None = None, limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = select(Invoice).order_by(Invoice.created_at.desc()).limit(limit).offset(offset)
    if user.role == "student":
        if student_id is not None and student_id != user.student_id:
            raise HTTPException(status_code=403, detail="Students can only view their own invoices")
        query = query.where(Invoice.student_id == user.student_id)
    elif student_id:
        query = query.where(Invoice.student_id == student_id)
    if course_id:
        query = query.where(Invoice.course_id == course_id)
    return db.scalars(query).all()


@router.get("/invoices/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    invoice = db.get(Invoice, invoice_id)
    if not invoice or (user.role == "student" and invoice.student_id != user.student_id):
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.get("/usage-records/{usage_id}/invoice", response_model=InvoiceOut)
def get_usage_invoice(usage_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    invoice = db.scalar(select(Invoice).where(Invoice.usage_record_id == usage_id))
    if not invoice or (user.role == "student" and invoice.student_id != user.student_id):
        raise HTTPException(status_code=404, detail="Invoice not found for usage record")
    return invoice
