from fastapi import APIRouter, HTTPException
from database import supabase

router = APIRouter(prefix="/scorecard", tags=["Module 5 - Vendor Scorecard"])


@router.get("/{vendor_id}")
def get_scorecard(vendor_id: str):
    vendor = supabase.table("qprocure_vendors").select("*").eq("id", vendor_id).execute()
    if not vendor.data:
        raise HTTPException(status_code=404, detail="Vendor not found")

    score = supabase.table("qprocure_vendor_scores").select("*").eq("vendor_id", vendor_id).execute()
    quote_history = (
        supabase.table("qprocure_rfq_responses")
        .select("*, qprocure_rfqs(rfq_number)")
        .eq("vendor_id", vendor_id)
        .execute()
        .data
    )

    return {
        "vendor": vendor.data[0],
        "scores": score.data[0] if score.data else None,
        "quote_history": quote_history,
    }


@router.post("/{vendor_id}/recalculate")
def recalculate_score(vendor_id: str):
    dispatch = supabase.table("qprocure_rfq_dispatch").select("*").eq("vendor_id", vendor_id).execute().data
    responses = supabase.table("qprocure_rfq_responses").select("*").eq("vendor_id", vendor_id).execute().data

    total_sent = len(dispatch)
    total_responded = len(responses)
    response_rate = round((total_responded / total_sent) * 100, 1) if total_sent else 0

    scores_row = {
        "vendor_id": vendor_id,
        "response_rate": response_rate,
        "avg_response_hours": None,
        "on_time_delivery_pct": None,
        "price_vs_ref_pct": None,
        "responsiveness_stars": min(5, round(response_rate / 20)),
        "price_competitiveness_stars": None,
        "delivery_reliability_stars": None,
        "compliance_stars": None,
    }

    existing = supabase.table("qprocure_vendor_scores").select("vendor_id").eq("vendor_id", vendor_id).execute()
    if existing.data:
        supabase.table("qprocure_vendor_scores").update(scores_row).eq("vendor_id", vendor_id).execute()
    else:
        supabase.table("qprocure_vendor_scores").insert(scores_row).execute()

    return scores_row