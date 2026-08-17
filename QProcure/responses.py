from fastapi import APIRouter, HTTPException
from database import supabase
from models import ResponseCreate
from imap_service import poll_inbox
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/responses", tags=["Module 4 - RFQ Response Dashboard"])


class QuoteFormSubmit(BaseModel):
    price: float
    moq: int
    lead_time_weeks: float
    condition: str
    warranty: str
    notes: Optional[str] = None


@router.get("/form/{dispatch_id}")
def get_quote_form_data(dispatch_id: str):
    """
    Called by the vendor-facing quote form to load RFQ + vendor context
    before showing the fields.
    """
    dispatch = supabase.table("qprocure_rfq_dispatch").select("*, qprocure_vendors(*)").eq("id", dispatch_id).execute()
    if not dispatch.data:
        raise HTTPException(status_code=404, detail="Invalid or expired link")
    d = dispatch.data[0]

    rfq = supabase.table("qprocure_rfqs").select("*").eq("id", d["rfq_id"]).execute()
    lines = supabase.table("qprocure_rfq_lines").select("*").eq("rfq_id", d["rfq_id"]).execute()

    already_responded = supabase.table("qprocure_rfq_responses").select("id") \
        .eq("rfq_id", d["rfq_id"]).eq("vendor_id", d["vendor_id"]).execute()

    return {
        "vendor_name": d["qprocure_vendors"]["name"],
        "rfq_number": rfq.data[0]["rfq_number"] if rfq.data else "Unknown",
        "rfq_title": rfq.data[0]["title"] if rfq.data else "",
        "lines": lines.data,
        "already_responded": len(already_responded.data) > 0,
    }


@router.post("/form/{dispatch_id}")
def submit_quote_form(dispatch_id: str, payload: QuoteFormSubmit):
    """
    Vendor-facing form submission - structured data, no email parsing needed.
    """
    dispatch = supabase.table("qprocure_rfq_dispatch").select("*").eq("id", dispatch_id).execute()
    if not dispatch.data:
        raise HTTPException(status_code=404, detail="Invalid or expired link")
    d = dispatch.data[0]

    row = {
        "rfq_id": d["rfq_id"],
        "vendor_id": d["vendor_id"],
        "raw_email_body": payload.notes or "(submitted via form)",
        "price": payload.price,
        "moq": payload.moq,
        "lead_time_weeks": payload.lead_time_weeks,
        "condition": payload.condition,
        "warranty": payload.warranty,
        "extraction_status": "auto_parsed",
    }
    result = supabase.table("qprocure_rfq_responses").insert(row).execute()
    return result.data[0]


@router.post("/poll-inbox")
def trigger_inbox_poll():
    """
    Manually triggers an IMAP inbox check for new vendor replies.
    Kept as a fallback for vendors who reply by email instead of
    using the quote form link.
    """
    try:
        inserted = poll_inbox()
        return {"new_responses": len(inserted), "responses": inserted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"IMAP poll failed: {str(e)}")


@router.post("")
def add_response(payload: ResponseCreate):
    """
    For now, replies are pasted in manually (raw_email_body) along with
    parsed price/moq/lead_time if known. Once inbound email + an
    extraction step is wired up, this can be called automatically.
    """
    extraction_status = "auto_parsed" if payload.price is not None else "needs_verify"

    row = {
        "rfq_id": payload.rfq_id,
        "vendor_id": payload.vendor_id,
        "raw_email_body": payload.raw_email_body,
        "price": payload.price,
        "moq": payload.moq,
        "lead_time_weeks": payload.lead_time_weeks,
        "extraction_status": extraction_status,
    }
    result = supabase.table("qprocure_rfq_responses").insert(row).execute()
    return result.data[0]


@router.get("/{rfq_id}")
def get_dashboard(rfq_id: str):
    """
    Returns the response dashboard data: all dispatched vendors,
    whether they've responded, and sorted by price (best first).
    """
    dispatch = supabase.table("qprocure_rfq_dispatch").select("*, qprocure_vendors(*)").eq("rfq_id", rfq_id).execute().data
    responses = supabase.table("qprocure_rfq_responses").select("*").eq("rfq_id", rfq_id).execute().data

    responses_by_vendor = {r["vendor_id"]: r for r in responses}

    rows = []
    for d in dispatch:
        vendor = d["qprocure_vendors"]
        resp = responses_by_vendor.get(d["vendor_id"])
        rows.append({
            "vendor_id": vendor["id"],
            "vendor_name": vendor["name"],
            "rating": vendor["rating"],
            "channel": d["channel"],
            "responded": resp is not None,
            "price": resp["price"] if resp else None,
            "moq": resp["moq"] if resp else None,
            "lead_time_weeks": resp["lead_time_weeks"] if resp else None,
            "extraction_status": resp["extraction_status"] if resp else "unread",
            "response_id": resp["id"] if resp else None,
        })

    rows.sort(key=lambda r: (r["price"] is None, r["price"] or 0))

    responded_count = sum(1 for r in rows if r["responded"])
    return {
        "vendors_responded": f"{responded_count}/{len(rows)}",
        "needs_manual_review": sum(1 for r in rows if r["extraction_status"] == "needs_verify"),
        "best_price": next((r["price"] for r in rows if r["price"] is not None), None),
        "rows": rows,
    }