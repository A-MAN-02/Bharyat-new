from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ---------- Module 1: Vendors ----------
class VendorCreate(BaseModel):
    name: str
    category: Optional[str] = None
    region: Optional[str] = None
    email: str
    rating: str = "C"


class VendorOut(VendorCreate):
    id: str
    rating: str = "C"
    created_at: Optional[datetime] = None


# ---------- Module 2: RFQ creation ----------
class RFQLineIn(BaseModel):
    part_number: str
    qty: int
    target_price: Optional[float] = None
    notes: Optional[str] = None


class RFQCreate(BaseModel):
    rfq_number: str
    title: Optional[str] = None
    template: str = "standard_component_rfq"
    created_by: Optional[str] = None
    lines: List[RFQLineIn]


class RFQOut(BaseModel):
    id: str
    rfq_number: str
    title: Optional[str]
    status: str
    created_at: Optional[datetime] = None


# ---------- Module 3: Dispatch ----------
class DispatchRequest(BaseModel):
    rfq_id: str
    vendor_ids: List[str]
    message_body: str            # rendered RFQ email body
    schedule_reminder_hours: Optional[int] = 48


# ---------- Module 4: Responses ----------
class ResponseCreate(BaseModel):
    rfq_id: str
    vendor_id: str
    raw_email_body: str
    price: Optional[float] = None
    moq: Optional[int] = None
    lead_time_weeks: Optional[float] = None


class ResponseOut(BaseModel):
    id: str
    vendor_id: str
    price: Optional[float]
    moq: Optional[int]
    lead_time_weeks: Optional[float]
    extraction_status: str


# ---------- Module 6: Award / PO ----------
class AwardRequest(BaseModel):
    rfq_id: str
    vendor_id: str
    response_id: str
    justification: str            # lowest_price | best_rating | fastest_lead_time
    justification_note: Optional[str] = None
    requested_documents: List[str] = []
    po_number: Optional[str] = None
