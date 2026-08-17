import os
import base64
import resend

resend.api_key = os.environ.get("RESEND_API_KEY", "")
FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "rfq@bharyat.com")

# Base URL where quote_form.html is hosted (update once deployed, e.g. https://bharyat.com/qprocure)
FORM_BASE_URL = os.environ.get("QUOTE_FORM_BASE_URL", "http://localhost:5500/quote_form.html")


def send_rfq_email(to_email: str, subject: str, html_body: str) -> str:
    """
    Sends an RFQ email via Resend. Returns the Resend email id
    (used to correlate later, e.g. for tracking / reminders).
    """
    response = resend.Emails.send({
        "from": FROM_EMAIL,
        "to": [to_email],
        "subject": subject,
        "html": html_body,
    })
    return response.get("id", "")


def send_po_email(to_email: str, subject: str, vendor_name: str, po_number: str, pdf_bytes: bytes) -> str:
    """
    Sends the Purchase Order to the vendor as a PDF attachment via Resend.
    """
    html_body = f"""
    <p>Dear {vendor_name},</p>
    <p>Please find attached Purchase Order <strong>{po_number}</strong> from
    Bharyat Advanced Systems Pvt. Ltd.</p>
    <p>Kindly confirm receipt and share your expected delivery timeline.</p>
    <p>Regards,<br>Bharyat Advanced Systems Pvt. Ltd.</p>
    """
    encoded_pdf = base64.b64encode(pdf_bytes).decode("utf-8")

    response = resend.Emails.send({
        "from": FROM_EMAIL,
        "to": [to_email],
        "subject": subject,
        "html": html_body,
        "attachments": [
            {"filename": f"{po_number}.pdf", "content": encoded_pdf}
        ],
    })
    return response.get("id", "")


def render_rfq_email(rfq_number: str, lines: list, vendor_name: str, dispatch_id: str) -> str:
    """
    RFQ email with a link to the quote form (instead of asking the
    vendor to reply with free-text price/MOQ/lead time).
    """
    rows = "".join(
        f"<tr><td>{l['part_number']}</td><td>{l['qty']}</td>"
        f"<td>{l.get('target_price') or '-'}</td></tr>"
        for l in lines
    )
    form_link = f"{FORM_BASE_URL}?d={dispatch_id}"
    return f"""
    <p>Dear {vendor_name},</p>
    <p>Please quote for the following components under RFQ {rfq_number}:</p>
    <table border="1" cellpadding="6" cellspacing="0">
      <tr><th>Part Number</th><th>Qty</th><th>Target Price</th></tr>
      {rows}
    </table>
    <p>
      <a href="{form_link}" style="background:#3b8ff0;color:#fff;padding:10px 20px;
         text-decoration:none;border-radius:6px;display:inline-block;">
         Submit your quote
      </a>
    </p>
    <p>Or copy this link into your browser: {form_link}</p>
    <p>Regards,<br>Bharyat Advanced Systems Pvt. Ltd.</p>
    """