from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_po_pdf(po_data: dict) -> bytes:
    """
    po_data expects:
      po_number, rfq_number, vendor_name, vendor_email,
      lines (list of {part_number, qty, target_price}),
      price, moq, lead_time_weeks, condition, warranty,
      justification, requested_documents (list)
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.6 * inch, bottomMargin=0.6 * inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], fontSize=18, spaceAfter=4)
    label_style = ParagraphStyle("LabelStyle", parent=styles["Normal"], textColor=colors.grey, fontSize=9)
    value_style = ParagraphStyle("ValueStyle", parent=styles["Normal"], fontSize=11, spaceAfter=8)

    story = []

    story.append(Paragraph("Bharyat Advanced Systems Pvt. Ltd.", title_style))
    story.append(Paragraph(f"Purchase Order — {po_data['po_number']}", styles["Heading2"]))
    story.append(Spacer(1, 12))

    # Header info table
    header_data = [
        ["RFQ Number:", po_data["rfq_number"], "Vendor:", po_data["vendor_name"]],
        ["MOQ:", str(po_data.get("moq", "-")), "Vendor Email:", po_data["vendor_email"]],
        ["Lead Time:", f"{po_data.get('lead_time_weeks', '-')} weeks", "Condition:", po_data.get("condition") or "-"],
        ["Warranty:", po_data.get("warranty") or "-", "Justification:", po_data.get("justification", "-").replace("_", " ").title()],
    ]
    header_table = Table(header_data, colWidths=[1.1 * inch, 2.1 * inch, 1.1 * inch, 2.1 * inch])
    header_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.grey),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.grey),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 16))

    # Line items table
    story.append(Paragraph("Line Items", styles["Heading3"]))
    line_rows = [["Part Number", "Qty", "Target Price", "Quoted Price"]]
    for line in po_data.get("lines", []):
        line_rows.append([
            line.get("part_number", "-"),
            str(line.get("qty", "-")),
            str(line.get("target_price") or "-"),
            f"{po_data.get('price', '-')}",
        ])
    lines_table = Table(line_rows, colWidths=[2.2 * inch, 1 * inch, 1.5 * inch, 1.5 * inch])
    lines_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3b8ff0")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(lines_table)
    story.append(Spacer(1, 16))

    # Requested documents
    docs = po_data.get("requested_documents") or []
    if docs:
        story.append(Paragraph("Required Documents", styles["Heading3"]))
        for d in docs:
            story.append(Paragraph(f"• {d}", value_style))
        story.append(Spacer(1, 12))

    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "This purchase order is issued by Bharyat Advanced Systems Pvt. Ltd. "
        "Please confirm receipt and expected delivery timeline.",
        label_style
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()