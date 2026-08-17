from fastapi import APIRouter, HTTPException
from database import supabase
from models import VendorCreate

router = APIRouter(prefix="/vendors", tags=["Module 1 - Vendor Directory"])


@router.get("")
def list_vendors(category: str = None, region: str = None, rating: str = None):
    query = supabase.table("qprocure_vendors").select("*")
    if category:
        query = query.eq("category", category)
    if region:
        query = query.eq("region", region)
    if rating:
        query = query.eq("rating", rating)
    result = query.execute()
    return result.data


@router.post("")
def create_vendor(vendor: VendorCreate):
    result = supabase.table("qprocure_vendors").insert(vendor.model_dump()).execute()
    return result.data[0]


@router.get("/{vendor_id}")
def get_vendor(vendor_id: str):
    result = supabase.table("qprocure_vendors").select("*").eq("id", vendor_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return result.data[0]


@router.delete("/{vendor_id}")
def delete_vendor(vendor_id: str):
    supabase.table("qprocure_vendors").delete().eq("id", vendor_id).execute()
    return {"status": "deleted"}