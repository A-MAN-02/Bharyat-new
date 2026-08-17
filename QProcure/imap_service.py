"""
Fallback path: polls the RFQ mailbox via IMAP for vendors who reply
by email instead of using the quote form link. The quote form is now
the primary path (see responses.py /form/{dispatch_id}).
"""

import os
import re
import imaplib
import email
from email.header import decode_header
from database import supabase

IMAP_HOST = os.environ.get("IMAP_HOST", "imap.hostinger.com")
IMAP_PORT = int(os.environ.get("IMAP_PORT", "993"))
IMAP_USER = os.environ.get("IMAP_USER", "rfq@bharyat.com")
IMAP_PASS = os.environ.get("IMAP_PASS", "")

RFQ_NUMBER_RE = re.compile(r"RFQ[\s\-]?(\d+)", re.IGNORECASE)
PRICE_RE = re.compile(r"(?:price|rate)[^\d₹$]{0,15}([\d,]+(?:\.\d+)?)", re.IGNORECASE)
MOQ_RE = re.compile(r"MOQ[^\d]{0,10}([\d,]+)", re.IGNORECASE)
LEAD_TIME_RE = re.compile(r"lead[\s\-]?time[^\d]{0,10}([\d.]+)\s*(week|day)", re.IGNORECASE)


def _decode(value):
    if not value:
        return ""
    parts = decode_header(value)
    return "".join(
        p.decode(enc or "utf-8", errors="ignore") if isinstance(p, bytes) else p
        for p, enc in parts
    )


def _get_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode(errors="ignore")
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                return part.get_payload(decode=True).decode(errors="ignore")
        return ""
    return msg.get_payload(decode=True).decode(errors="ignore")


def extract_fields(body: str):
    price = None
    moq = None
    lead_time_weeks = None

    price_match = PRICE_RE.search(body)
    if price_match:
        price = float(price_match.group(1).replace(",", ""))

    moq_match = MOQ_RE.search(body)
    if moq_match:
        moq = int(moq_match.group(1).replace(",", ""))

    lead_match = LEAD_TIME_RE.search(body)
    if lead_match:
        value, unit = float(lead_match.group(1)), lead_match.group(2).lower()
        lead_time_weeks = value / 7 if unit == "day" else value

    return price, moq, lead_time_weeks


def poll_inbox(mark_seen: bool = True) -> list:
    inserted = []

    imap = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    imap.login(IMAP_USER, IMAP_PASS)
    imap.select("INBOX")

    status, message_ids = imap.search(None, "UNSEEN")
    if status != "OK":
        imap.logout()
        return inserted

    for msg_id in message_ids[0].split():
        status, msg_data = imap.fetch(msg_id, "(BODY.PEEK[])")
        if status != "OK":
            continue

        raw_msg = email.message_from_bytes(msg_data[0][1])
        subject = _decode(raw_msg.get("Subject"))
        from_addr = email.utils.parseaddr(raw_msg.get("From"))[1].strip().lower()
        body = _get_body(raw_msg)

        rfq_match = RFQ_NUMBER_RE.search(subject) or RFQ_NUMBER_RE.search(body)
        if not rfq_match:
            continue

        rfq_number = f"RFQ-{rfq_match.group(1)}"
        rfq_result = supabase.table("qprocure_rfqs").select("id").eq("rfq_number", rfq_number).execute()
        if not rfq_result.data:
            continue
        rfq_id = rfq_result.data[0]["id"]

        all_vendors = supabase.table("qprocure_vendors").select("id, email").execute().data
        vendor_id = next(
            (v["id"] for v in all_vendors if v["email"].strip().lower() == from_addr),
            None
        )
        if not vendor_id:
            continue

        price, moq, lead_time_weeks = extract_fields(body)
        extraction_status = "auto_parsed" if price is not None else "needs_verify"

        row = {
            "rfq_id": rfq_id,
            "vendor_id": vendor_id,
            "raw_email_body": body,
            "price": price,
            "moq": moq,
            "lead_time_weeks": lead_time_weeks,
            "extraction_status": extraction_status,
        }
        result = supabase.table("qprocure_rfq_responses").insert(row).execute()
        inserted.append(result.data[0])

        if mark_seen:
            imap.store(msg_id, '+FLAGS', '\\Seen')

    imap.logout()
    return inserted


if __name__ == "__main__":
    results = poll_inbox()
    print(f"Inserted {len(results)} response(s)")