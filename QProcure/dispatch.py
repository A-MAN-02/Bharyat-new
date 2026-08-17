from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from database import supabase
from models import DispatchRequest
from email_service import send_rfq_email, render_rfq_email

router = APIRouter(prefix="/dispatch", tags=["Module 3 - Vendor Selection & Dispatch"])


@router.post("")
def dispatch_rfq(payload: DispatchRequest):
    rfq = supabase.table("qprocure_rfqs").select("*").eq("id", payload.rfq_id).execute()
    if not rfq.data:
        raise HTTPException(status_code=404, detail="RFQ not found")
    rfq_number = rfq.data[0]["rfq_number"]

    lines = supabase.table("qprocure_rfq_lines").select("*").eq("rfq_id", payload.rfq_id).execute().data

    results = []
    for vendor_id in payload.vendor_ids:
        vendor = supabase.table("qprocure_vendors").select("*").eq("id", vendor_id).execute()
        if not vendor.data:
            continue
        vendor = vendor.data[0]

        # Create the dispatch row first (status=pending) so we have an id
        # to embed in the quote-form link before the email goes out.
        dispatch_row = {
            "rfq_id": payload.rfq_id,
            "vendor_id": vendor_id,
            "channel": "email",
            "status": "pending",
        }
        created = supabase.table("qprocure_rfq_dispatch").insert(dispatch_row).execute().data[0]
        dispatch_id = created["id"]

        html_body = render_rfq_email(rfq_number, lines, vendor["name"], dispatch_id)

        update_data = {}
        try:
            email_id = send_rfq_email(
                to_email=vendor["email"],
                subject=f"RFQ {rfq_number} - Request for Quotation",
                html_body=html_body,
            )
            update_data["status"] = "sent"
            update_data["sent_at"] = datetime.utcnow().isoformat()
            update_data["resend_email_id"] = email_id
            if payload.schedule_reminder_hours:
                update_data["reminder_at"] = (
                    datetime.utcnow() + timedelta(hours=payload.schedule_reminder_hours)
                ).isoformat()
        except Exception as e:
            update_data["status"] = "failed"

        result = supabase.table("qprocure_rfq_dispatch").update(update_data).eq("id", dispatch_id).execute()
        results.append(result.data[0])

    supabase.table("qprocure_rfqs").update({"status": "dispatched"}).eq("id", payload.rfq_id).execute()
    return {"dispatched": results}


@router.get("/{rfq_id}")
def get_dispatch_status(rfq_id: str):
    result = supabase.table("qprocure_rfq_dispatch").select("*, qprocure_vendors(*)").eq("rfq_id", rfq_id).execute()
    return result.data