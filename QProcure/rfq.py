from fastapi import APIRouter, HTTPException
from database import supabase
from models import RFQCreate

router = APIRouter(prefix="/rfq", tags=["Module 2 - RFQ Creation"])


@router.post("")
def create_rfq(payload: RFQCreate):
    rfq_data = {
        "rfq_number": payload.rfq_number,
        "title": payload.title,
        "template": payload.template,
        "created_by": payload.created_by,
        "status": "draft",
    }
    rfq_result = supabase.table("qprocure_rfqs").insert(rfq_data).execute()
    rfq = rfq_result.data[0]

    lines_data = [
        {
            "rfq_id": rfq["id"],
            "part_number": l.part_number,
            "qty": l.qty,
            "target_price": l.target_price,
            "notes": l.notes,
        }
        for l in payload.lines
    ]
    if lines_data:
        supabase.table("qprocure_rfq_lines").insert(lines_data).execute()

    return rfq


@router.get("")
def list_rfqs(status: str = None):
    query = supabase.table("qprocure_rfqs").select("*")
    if status:
        query = query.eq("status", status)
    result = query.order("created_at", desc=True).execute()
    return result.data


@router.get("/{rfq_id}")
def get_rfq(rfq_id: str):
    rfq = supabase.table("qprocure_rfqs").select("*").eq("id", rfq_id).execute()
    if not rfq.data:
        raise HTTPException(status_code=404, detail="RFQ not found")
    lines = supabase.table("qprocure_rfq_lines").select("*").eq("rfq_id", rfq_id).execute()
    return {**rfq.data[0], "lines": lines.data}


@router.put("/{rfq_id}/status")
def update_status(rfq_id: str, status: str):
    supabase.table("qprocure_rfqs").update({"status": status}).eq("id", rfq_id).execute()
    return {"status": "updated"}