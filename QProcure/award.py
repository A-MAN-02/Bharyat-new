from datetime import datetime
from fastapi import APIRouter, HTTPException
from database import supabase
from models import AwardRequest
from pdf_service import generate_po_pdf
from email_service import send_po_email

router = APIRouter(prefix="/award", tags=["Module 6 - Award & PO Conversion"])


@router.post("")
def create_award(payload: AwardRequest):
    row = {
        "rfq_id": payload.rfq_id,
        "vendor_id": payload.vendor_id,
        "response_id": payload.response_id,
        "justification": payload.justification,
        "justification_note": payload.justification_note,
        "requested_documents": payload.requested_documents,
        "po_number": payload.po_number,
        "po_status": "draft",
    }
    result = supabase.table("qprocure_awards").insert(row).execute()
    supabase.table("qprocure_rfqs").update({"status": "awarded"}).eq("id", payload.rfq_id).execute()
    return result.data[0]


@router.get("/{rfq_id}/preview")
def get_po_preview(rfq_id: str):
    """
    Full data needed to render the PO preview screen before sending:
    vendor info, RFQ line items, the winning quote (price/moq/lead time/
    condition/warranty), justification, and requested documents.
    """
    award = supabase.table("qprocure_awards").select("*, qprocure_vendors(*)").eq("rfq_id", rfq_id).execute()
    if not award.data:
        raise HTTPException(status_code=404, detail="No award found for this RFQ")
    a = award.data[0]

    rfq = supabase.table("qprocure_rfqs").select("*").eq("id", rfq_id).execute()
    if not rfq.data:
        raise HTTPException(status_code=404, detail="RFQ not found")
    rfq = rfq.data[0]

    lines = supabase.table("qprocure_rfq_lines").select("*").eq("rfq_id", rfq_id).execute().data

    response = supabase.table("qprocure_rfq_responses").select("*").eq("id", a["response_id"]).execute()
    response = response.data[0] if response.data else {}

    return {
        "award_id": a["id"],
        "po_number": a["po_number"] or f"PO-{a['id'][:8].upper()}",
        "po_status": a["po_status"],
        "rfq_number": rfq["rfq_number"],
        "vendor": a["qprocure_vendors"],
        "lines": lines,
        "price": response.get("price"),
        "moq": response.get("moq"),
        "lead_time_weeks": response.get("lead_time_weeks"),
        "condition": response.get("condition"),
        "warranty": response.get("warranty"),
        "justification": a["justification"],
        "justification_note": a["justification_note"],
        "requested_documents": a["requested_documents"],
    }


@router.put("/{award_id}/send-po")
def send_po(award_id: str):
    """
    Generates the PO as a PDF and emails it to the vendor via Resend,
    then marks the award as sent.
    """
    award = supabase.table("qprocure_awards").select("*, qprocure_vendors(*)").eq("id", award_id).execute()
    if not award.data:
        raise HTTPException(status_code=404, detail="Award not found")
    a = award.data[0]

    rfq = supabase.table("qprocure_rfqs").select("*").eq("id", a["rfq_id"]).execute().data[0]
    lines = supabase.table("qprocure_rfq_lines").select("*").eq("rfq_id", a["rfq_id"]).execute().data
    response = supabase.table("qprocure_rfq_responses").select("*").eq("id", a["response_id"]).execute()
    response = response.data[0] if response.data else {}

    po_number = a["po_number"] or f"PO-{a['id'][:8].upper()}"

    po_data = {
        "po_number": po_number,
        "rfq_number": rfq["rfq_number"],
        "vendor_name": a["qprocure_vendors"]["name"],
        "vendor_email": a["qprocure_vendors"]["email"],
        "lines": lines,
        "price": response.get("price"),
        "moq": response.get("moq"),
        "lead_time_weeks": response.get("lead_time_weeks"),
        "condition": response.get("condition"),
        "warranty": response.get("warranty"),
        "justification": a["justification"],
        "requested_documents": a["requested_documents"],
    }

    pdf_bytes = generate_po_pdf(po_data)

    send_po_email(
        to_email=a["qprocure_vendors"]["email"],
        subject=f"Purchase Order {po_number} - Bharyat Advanced Systems",
        vendor_name=a["qprocure_vendors"]["name"],
        po_number=po_number,
        pdf_bytes=pdf_bytes,
    )

    result = supabase.table("qprocure_awards").update(
        {"po_status": "sent", "po_number": po_number}
    ).eq("id", award_id).execute()
    return result.data[0]


@router.get("/{rfq_id}")
def get_award(rfq_id: str):
    result = supabase.table("qprocure_awards").select("*, qprocure_vendors(*)").eq("rfq_id", rfq_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="No award found for this RFQ")
    return result.data[0]