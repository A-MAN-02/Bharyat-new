import json
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from database import supabase

router = APIRouter(prefix="/vendor-registration", tags=["Module 7 - Vendor Registration"])

BUCKET = "vendor-documents"


@router.post("")
async def create_registration(
    company_name: str = Form(...),
    country: str = Form(...),
    location: str = Form(...),
    website: str = Form(...),
    year_established: int = Form(...),
    email: str = Form(...),

    vendor_type: str = Form(...),

    component_tags: str = Form(...),
    brands_line_card: str = Form(...),

    company_registration_number: str = Form(...),
    gst_vat: str = Form(...),
    quality_certificates: str = Form(...),
    iso_certified: str = Form(...),
    references_info: str = Form(...),

    payment_terms: str = Form(...),
    credit_terms: str = Form(...),
    moq: int = Form(...),
    freight_terms: str = Form(...),
    warranty: str = Form(...),
    accepted_currencies: str = Form(...),

    bank_name: str = Form(...),
    account_number: str = Form(...),
    swift_ifsc: str = Form(...),
    billing_currency: str = Form(...),

    market_capability: str = Form(...),
    geography: str = Form(...),

    compliance_risk_rating: str = Form(...),
    compliance_notes: Optional[str] = Form(None),

    contacts: str = Form(...),

    company_profile_ppt: UploadFile = File(...),
    certificate_of_incorporation: UploadFile = File(...),
    iso_quality_certificate: UploadFile = File(...),
    rohs_reach_declaration: UploadFile = File(...),
    insurance_certificate: UploadFile = File(...),
    line_card_attachment: Optional[UploadFile] = File(None),
):
    vendor_row = {
        "name": company_name,
        "email": email,
        "category": None,
        "region": country,
        "rating": "C",
    }
    vendor = supabase.table("qprocure_vendors").insert(vendor_row).execute().data[0]
    vendor_id = vendor["id"]

    try:
        component_tags_list = json.loads(component_tags)
        market_capability_list = json.loads(market_capability)
        geography_list = json.loads(geography)
        contacts_list = json.loads(contacts)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="component_tags, market_capability, geography, and contacts must be valid JSON arrays")

    registration_row = {
        "vendor_id": vendor_id,
        "company_name": company_name,
        "country": country,
        "location": location,
        "website": website,
        "year_established": year_established,
        "vendor_type": vendor_type,
        "component_tags": component_tags_list,
        "brands_line_card": brands_line_card,
        "company_registration_number": company_registration_number,
        "gst_vat": gst_vat,
        "quality_certificates": quality_certificates,
        "iso_certified": iso_certified,
        "references_info": references_info,
        "payment_terms": payment_terms,
        "credit_terms": credit_terms,
        "moq": moq,
        "freight_terms": freight_terms,
        "warranty": warranty,
        "accepted_currencies": accepted_currencies,
        "bank_name": bank_name,
        "account_number": account_number,
        "swift_ifsc": swift_ifsc,
        "billing_currency": billing_currency,
        "market_capability": market_capability_list,
        "geography": geography_list,
        "compliance_risk_rating": compliance_risk_rating,
        "compliance_notes": compliance_notes,
    }
    supabase.table("qprocure_vendor_registrations").insert(registration_row).execute()

    if contacts_list:
        contact_rows = [
            {
                "vendor_id": vendor_id,
                "name": c["name"],
                "role": c["role"],
                "email": c["email"],
                "phone": c["phone"],
                "whatsapp": c["whatsapp"],
                "preferred_channel": c["preferred_channel"],
            }
            for c in contacts_list
        ]
        supabase.table("qprocure_vendor_contacts").insert(contact_rows).execute()

    doc_files = {
        "Company Profile PPT": company_profile_ppt,
        "Certificate of Incorporation": certificate_of_incorporation,
        "ISO / Quality Certificate": iso_quality_certificate,
        "RoHS / REACH Declaration": rohs_reach_declaration,
        "Insurance Certificate": insurance_certificate,
    }
    if line_card_attachment is not None and line_card_attachment.filename:
        doc_files["Line Card Attachment"] = line_card_attachment

    for doc_type, upload in doc_files.items():
        contents = await upload.read()
        ext = upload.filename.split(".")[-1] if "." in upload.filename else "bin"
        storage_path = f"{vendor_id}/{uuid.uuid4()}.{ext}"

        supabase.storage.from_(BUCKET).upload(
            storage_path, contents,
            {"content-type": upload.content_type or "application/octet-stream"}
        )

        supabase.table("qprocure_vendor_documents").insert({
            "vendor_id": vendor_id,
            "doc_type": doc_type,
            "file_name": upload.filename,
            "storage_path": storage_path,
        }).execute()

    return {"vendor_id": vendor_id, "status": "registered"}


@router.get("")
def list_registrations():
    result = supabase.table("qprocure_vendor_registrations").select("*, qprocure_vendors(name, email, rating)").execute()
    return result.data


@router.get("/{vendor_id}")
def get_registration(vendor_id: str):
    reg = supabase.table("qprocure_vendor_registrations").select("*").eq("vendor_id", vendor_id).execute()
    if not reg.data:
        raise HTTPException(status_code=404, detail="Registration not found")

    contacts = supabase.table("qprocure_vendor_contacts").select("*").eq("vendor_id", vendor_id).execute()
    documents = supabase.table("qprocure_vendor_documents").select("*").eq("vendor_id", vendor_id).execute()

    docs_with_urls = []
    for d in documents.data:
        url = supabase.storage.from_(BUCKET).create_signed_url(d["storage_path"], 3600)
        docs_with_urls.append({**d, "signed_url": url.get("signedURL") if isinstance(url, dict) else None})

    return {
        "registration": reg.data[0],
        "contacts": contacts.data,
        "documents": docs_with_urls,
    }