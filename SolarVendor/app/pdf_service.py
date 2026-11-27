"""
PDF Generation Service using ReportLab.
Creates high-aesthetic, professional, official Solar Quotations, Proforma Invoices & GST Tax Invoices.
"""

import io
import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm

def get_theme_colors():
    return {
        "primary": colors.HexColor("#0f766e"),      # Deep Solar Teal
        "primary_dark": colors.HexColor("#115e59"),
        "secondary": colors.HexColor("#f59e0b"),    # Solar Amber
        "proforma": colors.HexColor("#1d4ed8"),     # Royal Blue for Proforma Invoice
        "dark": colors.HexColor("#1e293b"),         # Slate 800
        "light_bg": colors.HexColor("#f8fafc"),     # Slate 50
        "border": colors.HexColor("#e2e8f0"),       # Slate 200
        "text_muted": colors.HexColor("#64748b"),
        "success": colors.HexColor("#10b981")
    }

def generate_quotation_pdf(quote_data: dict, company: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    theme = get_theme_colors()
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=theme["primary"]
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=theme["text_muted"]
    )
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=theme["primary_dark"]
    )
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=theme["dark"]
    )
    bold_body = ParagraphStyle(
        'CustomBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=theme["dark"]
    )
    highlight_val = ParagraphStyle(
        'HighlightVal',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=theme["primary"]
    )

    elements = []

    # 1. Company Header
    header_data = [
        [
            Paragraph(f"<b>{company.get('company_name', 'SuryaTech Clean Energy Solutions')}</b><br/>"
                      f"<font color='#64748b' size='8'>{company.get('tagline', 'Empowering Homes & Businesses with Smart Rooftop Solar')}</font><br/>"
                      f"<font size='8'>{company.get('address', 'Plot No. 402, Saheed Nagar, Bhubaneswar, Odisha - 751007')}<br/>"
                      f"Phone: {company.get('phone', '+91 90000 00000')} | Email: {company.get('email', 'sales@suryatechenergy.com')}<br/>"
                      f"GSTIN: <b>{company.get('gstin', '21AAECS9876Q1Z8')}</b> | PAN: <b>{company.get('pan', 'AAECS9876Q')}</b></font>", body_style),
            Paragraph(f"<font color='#0f766e' size='16'><b>SOLAR PROPOSAL & QUOTATION</b></font><br/>"
                      f"<b>Quote Ref:</b> {quote_data.get('quote_no', 'QT-2026-0001')}<br/>"
                      f"<b>Date:</b> {datetime.now().strftime('%d-%b-%Y')}<br/>"
                      f"<b>Validity:</b> {quote_data.get('validity_days', 15)} Days<br/>"
                      f"<b>Status:</b> <font color='#059669'><b>{quote_data.get('status', 'Sent').upper()}</b></font>", body_style)
        ]
    ]
    htable = Table(header_data, colWidths=[310, 210])
    htable.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(htable)
    elements.append(HRFlowable(width="100%", thickness=1.5, color=theme["primary"], spaceAfter=10, spaceBefore=4))

    # 2. Customer & System Summary
    customer_info = (
        f"<b>PROPOSAL PREPARED FOR:</b><br/>"
        f"<b>Name:</b> {quote_data.get('customer_name', 'Customer')}<br/>"
        f"<b>Phone:</b> {quote_data.get('phone', 'N/A')}<br/>"
        f"<b>Address:</b> {quote_data.get('address', '')}, {quote_data.get('city', 'Odisha')}<br/>"
        f"<b>DISCOM:</b> {quote_data.get('discom', 'TPCODL')} | <b>Consumer No:</b> {quote_data.get('consumer_no', 'N/A')}<br/>"
        f"<b>Sanctioned Load:</b> {quote_data.get('sanctioned_load', 5.0)} kW ({quote_data.get('category', 'Residential')})"
    )
    system_summary = (
        f"<b>PROPOSED SOLAR SYSTEM:</b><br/>"
        f"<b>System Size:</b> <font color='#0f766e' size='11'><b>{quote_data.get('capacity_kw', 5.0)} kW On-Grid</b></font><br/>"
        f"<b>PV Modules:</b> {quote_data.get('panel_qty', 10)}x {quote_data.get('panel_make', '550Wp Mono PERC')}<br/>"
        f"<b>Inverter:</b> {quote_data.get('inverter_make', 'On-Grid Solar Inverter')}<br/>"
        f"<b>Daily Generation:</b> ~{quote_data.get('daily_generation_kwh', 21.0)} Units / Day<br/>"
        f"<b>Est. Monthly Generation:</b> ~{quote_data.get('monthly_generation_kwh', 625)} Units (₹{quote_data.get('monthly_savings', 3750):,.0f}/mo saved)"
    )

    info_table = Table([[Paragraph(customer_info, body_style), Paragraph(system_summary, body_style)]], colWidths=[260, 260])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), theme["light_bg"]),
        ('BOX', (0,0), (-1,-1), 0.5, theme["border"]),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 10))

    # 3. Bill of Materials (BOM)
    elements.append(Paragraph("<b>1. Detailed Technical Specifications & Bill of Materials (BOM)</b>", heading_style))
    elements.append(Spacer(1, 4))

    bom_rows = [
        ["Component", "Description / Specification", "Quantity", "Warranty"],
        [
            "Solar PV Modules",
            f"{quote_data.get('panel_make', '550Wp Mono PERC Bifacial')}\nHigh-efficiency Tier-1 ALMM approved, 144 Half-cut cells",
            f"{quote_data.get('panel_qty', 10)} Nos",
            "12 Yr Product\n25 Yr Performance"
        ],
        [
            "Grid-Tied Inverter",
            f"{quote_data.get('inverter_make', 'On-Grid String Inverter')}\nMPPT efficiency >98.6%, WiFi/GPRS live mobile app monitoring",
            "1 Unit",
            "5-10 Years Manufacturer"
        ],
        [
            "Module Mounting Structure",
            f"{quote_data.get('structure_type', 'HDG Standard Rooftop')}\nHot Dip Galvanized 80μm, 150 km/h wind certified",
            "Custom Lot",
            "10 Years Structural"
        ],
        [
            "Balance of System (BOS)",
            f"{quote_data.get('bos_details', 'Polycab/Havells UV DC Cable 4sqmm, Type-II SPD, MCBs, IP65 Enclosures')}",
            "1 Lot",
            "2 Years Workmanship"
        ],
        [
            "Earthing & Surge Protection",
            "3-Pit Chemical Earthing (Inverter, Structure, Surge) + Copper Lightning Arrester",
            "Complete",
            "5 Years"
        ],
        [
            "DISCOM & Net Metering",
            f"End-to-end documentation, testing, joint inspection & commissioning with {quote_data.get('discom', 'DISCOM')}",
            "Complete Turnkey",
            "Included"
        ]
    ]

    bom_table = Table(
        [[Paragraph(cell, bold_body if r==0 else body_style) for cell in row] for r, row in enumerate(bom_rows)],
        colWidths=[120, 240, 70, 90]
    )
    bom_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), theme["primary"]),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, theme["border"]),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    for i in range(len(bom_rows[0])):
        bom_table.setStyle(TableStyle([('TEXTCOLOR', (i,0), (i,0), colors.white)]))
    elements.append(bom_table)
    elements.append(Spacer(1, 10))

    # 4. Commercial & Financial Breakdown (Client specified 5% GST & non-GST extras)
    elements.append(Paragraph("<b>2. Commercial Cost Breakdown & Government Subsidy</b>", heading_style))
    elements.append(Spacer(1, 4))

    base_cost = quote_data.get('system_cost', 235000.0)
    gst_rate = quote_data.get('gst_rate', 5.0)
    gst_amt = quote_data.get('gst_amount', round(base_cost * (gst_rate / 100.0), 2))
    net_meter = quote_data.get('net_meter_cost', 3500.0)
    transport = quote_data.get('transportation_cost', 2500.0)
    total_cost = quote_data.get('total_project_cost', round(base_cost + gst_amt + net_meter + transport, 2))
    subsidy = quote_data.get('subsidy_eligible', 138000.0)
    net_cost = quote_data.get('net_customer_cost', max(0.0, round(total_cost - subsidy, 2)))

    pricing_rows = [
        ["Commercial Item", "Amount (₹)"],
        ["Base Solar Equipment & Turnkey Installation Cost", f"₹ {base_cost:,.2f}"],
        [f"Goods & Services Tax (GST @ {gst_rate}% on Solar Equipment)", f"₹ {gst_amt:,.2f}"],
        ["Net Meter & Bi-directional Meter Testing (Without GST)", f"₹ {net_meter:,.2f}"],
        ["Transportation & Site Logistics (Without GST)", f"₹ {transport:,.2f}"],
        ["TOTAL GROSS PROJECT TURNKEY VALUE", f"₹ {total_cost:,.2f}"],
        ["LESS: PM Surya Ghar + Odisha State Govt Subsidy (Direct DBT)*", f"- ₹ {subsidy:,.2f}"],
        ["NET ESTIMATED CUSTOMER INVESTMENT", f"₹ {net_cost:,.2f}"]
    ]

    price_table = Table(
        [[Paragraph(f"<b>{row[0]}</b>" if r in [0,5,7] else row[0], bold_body if r in [0,5,7] else body_style),
          Paragraph(f"<b>{row[1]}</b>" if r in [0,5,7] else row[1], highlight_val if r==7 else (bold_body if r in [0,5] else body_style))]
         for r, row in enumerate(pricing_rows)],
        colWidths=[360, 160]
    )
    price_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('GRID', (0,0), (-1,-1), 0.5, theme["border"]),
        ('BACKGROUND', (0,5), (-1,5), colors.HexColor("#f8fafc")),
        ('BACKGROUND', (0,6), (-1,6), colors.HexColor("#fef3c7")), # Amber highlight for subsidy
        ('BACKGROUND', (0,7), (-1,7), colors.HexColor("#dcfce7")), # Light Green for Net Cost
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(price_table)
    elements.append(Paragraph("<font size='7' color='#64748b'>* Central CFA ₹78,000 + Odisha State Solar Subsidy ₹60,000 = ₹1,38,000 credited directly to beneficiary bank account via National Portal post DISCOM net meter sync.</font>", body_style))
    elements.append(Spacer(1, 10))

    # 5. Milestone Payment Terms & Bank Details
    elements.append(Paragraph("<b>3. Payment Terms & Bank Details</b>", heading_style))
    terms_info = (
        "• <b>15% Advance Token:</b> Upon order booking and contract sign-off.<br/>"
        "• <b>60% Material Dispatch:</b> Upon dispatch of Solar Modules, Inverter & Structure to site.<br/>"
        "• <b>20% Installation Milestone:</b> Post completion of mounting, DC/AC cabling & testing.<br/>"
        "• <b>5% Final Settlement:</b> Upon DISCOM net meter installation and portal commissioning."
    )
    bank_info = (
        f"<b>BANK ACCOUNT FOR NEFT / RTGS / CHEQUE:</b><br/>"
        f"Beneficiary: <b>{company.get('company_name', 'SuryaTech Clean Energy')}</b><br/>"
        f"Bank: {company.get('bank_name', 'HDFC Bank Ltd')}<br/>"
        f"A/C No: <b>{company.get('account_no', '50200088991122')}</b> | IFSC: <b>{company.get('ifsc_code', 'HDFC0001234')}</b><br/>"
        f"UPI ID: <b>{company.get('upi_id', 'suryatech@hdfcbank')}</b>"
    )
    pay_table = Table([[Paragraph(terms_info, body_style), Paragraph(bank_info, body_style)]], colWidths=[260, 260])
    pay_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), theme["light_bg"]),
        ('BOX', (0,0), (-1,-1), 0.5, theme["border"]),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(pay_table)
    elements.append(Spacer(1, 12))

    # Signature Block
    sig_data = [
        [
            Paragraph("<b>Customer Acceptance:</b><br/><br/><br/>______________________<br/>Signature & Date", body_style),
            Paragraph(f"<b>For {company.get('company_name', 'SuryaTech Clean Energy Solutions')}</b><br/><br/><br/>______________________<br/>Authorized Signatory", body_style)
        ]
    ]
    sig_table = Table(sig_data, colWidths=[260, 260])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    elements.append(sig_table)

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generate_invoice_pdf(invoice_data: dict, company: dict) -> bytes:
    """
    Generates either a PROFORMA INVOICE or a TAX INVOICE depending on invoice_type.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    theme = get_theme_colors()
    styles = getSampleStyleSheet()

    body_style = ParagraphStyle(
        'InvBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=theme["dark"]
    )
    bold_body = ParagraphStyle(
        'InvBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=theme["dark"]
    )
    heading_style = ParagraphStyle(
        'InvHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=theme["primary_dark"]
    )

    elements = []

    inv_type = invoice_data.get('invoice_type', 'Tax Invoice')
    is_proforma = (inv_type == "Proforma Invoice" or str(invoice_data.get('invoice_no', '')).startswith('PI-'))

    header_title = "PROFORMA INVOICE" if is_proforma else "TAX INVOICE"
    header_color = "#1d4ed8" if is_proforma else "#0f766e" # Blue for Proforma, Teal for Tax Invoice

    # 1. Header
    header_data = [
        [
            Paragraph(f"<b>{company.get('company_name', 'SuryaTech Clean Energy Solutions')}</b><br/>"
                      f"<font size='8'>{company.get('address', 'Plot No. 402, Saheed Nagar, Bhubaneswar, Odisha - 751007')}<br/>"
                      f"Phone: {company.get('phone', '+91 90000 00000')} | Email: {company.get('email', 'sales@suryatechenergy.com')}<br/>"
                      f"GSTIN: <b>{company.get('gstin', '21AAECS9876Q1Z8')}</b> | PAN: <b>{company.get('pan', 'AAECS9876Q')}</b></font>", body_style),
            Paragraph(f"<font color='{header_color}' size='16'><b>{header_title}</b></font><br/>"
                      f"<b>Invoice No:</b> {invoice_data.get('invoice_no', 'INV-0000')}<br/>"
                      f"<b>Invoice Date:</b> {invoice_data.get('invoice_date', '')}<br/>"
                      f"<b>Due Date:</b> {invoice_data.get('due_date', '') or 'Due on Receipt'}<br/>"
                      f"<b>Status:</b> <font color='{'#10b981' if invoice_data.get('status') == 'Paid' else '#ef4444'}'><b>{invoice_data.get('status', 'Unpaid').upper()}</b></font>", body_style)
        ]
    ]
    htable = Table(header_data, colWidths=[310, 210])
    htable.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(htable)
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor(header_color), spaceAfter=10, spaceBefore=4))

    # 2. Bill To & Project Info
    bill_to_info = (
        f"<b>BILLED TO (CUSTOMER):</b><br/>"
        f"<b>Name:</b> {invoice_data.get('customer_name', 'Customer')}<br/>"
        f"<b>Address:</b> {invoice_data.get('address', '')}, {invoice_data.get('city', 'Odisha')}<br/>"
        f"<b>Phone:</b> {invoice_data.get('phone', 'N/A')}<br/>"
        f"<b>DISCOM Consumer No:</b> {invoice_data.get('consumer_no', 'N/A')}"
    )
    ship_to_info = (
        f"<b>INSTALLATION SITE / PROJECT:</b><br/>"
        f"<b>Project Code:</b> {invoice_data.get('project_code', 'PRJ-2026-0001')}<br/>"
        f"<b>Capacity:</b> {invoice_data.get('capacity_kw', 5.0)} kW Rooftop Solar<br/>"
        f"<b>DISCOM:</b> {invoice_data.get('discom', 'TPCODL')}<br/>"
        f"<b>Milestone:</b> {invoice_data.get('milestone_name', 'Advance Booking')}"
    )
    info_table = Table([[Paragraph(bill_to_info, body_style), Paragraph(ship_to_info, body_style)]], colWidths=[260, 260])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), theme["light_bg"]),
        ('BOX', (0,0), (-1,-1), 0.5, theme["border"]),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 10))

    # 3. Line Items Table (with 5% GST and optional Net Meter/Transport)
    base_amt = invoice_data.get('base_amount', 0.0)
    gst_rate = invoice_data.get('gst_rate', 5.0)
    gst_amt = invoice_data.get('gst_amount', round(base_amt * (gst_rate / 100.0), 2))
    cgst_rate = round(gst_rate / 2.0, 1) # 2.5%
    sgst_rate = round(gst_rate / 2.0, 1) # 2.5%
    cgst_amt = round(gst_amt / 2.0, 2)
    sgst_amt = round(gst_amt / 2.0, 2)
    net_meter = invoice_data.get('net_meter_cost', 0.0)
    transport = invoice_data.get('transportation_cost', 0.0)
    total_amt = invoice_data.get('total_amount', round(base_amt + gst_amt + net_meter + transport, 2))
    paid_amt = invoice_data.get('paid_amount', 0.0)
    balance_amt = max(0.0, round(total_amt - paid_amt, 2))

    line_items = [
        ["Sl", "Description of Goods & Services", "HSN/SAC", "Taxable Value (₹)", f"CGST ({cgst_rate}%)", f"SGST ({sgst_rate}%)", "Total (₹)"],
        [
            "1",
            f"Supply & Turnkey Installation of Rooftop Solar PV System\n• Milestone: {invoice_data.get('milestone_name', 'Milestone')}\n• Project Ref: {invoice_data.get('project_code', 'PRJ')}",
            "8461 / 9987",
            f"₹ {base_amt:,.2f}",
            f"₹ {cgst_amt:,.2f}",
            f"₹ {sgst_amt:,.2f}",
            f"₹ {(base_amt + gst_amt):,.2f}"
        ]
    ]

    sl = 2
    if net_meter and net_meter > 0:
        line_items.append([
            str(sl),
            "DISCOM Bi-directional Net Meter & Testing Charges (Non-GST)",
            "9987",
            f"₹ {net_meter:,.2f}",
            "₹ 0.00",
            "₹ 0.00",
            f"₹ {net_meter:,.2f}"
        ])
        sl += 1

    if transport and transport > 0:
        line_items.append([
            str(sl),
            "Site Transportation & Logistics Charges (Non-GST)",
            "9965",
            f"₹ {transport:,.2f}",
            "₹ 0.00",
            "₹ 0.00",
            f"₹ {transport:,.2f}"
        ])

    item_table = Table(
        [[Paragraph(cell, bold_body if r==0 else body_style) for cell in row] for r, row in enumerate(line_items)],
        colWidths=[24, 216, 60, 75, 55, 55, 75]
    )
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor(header_color)),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, theme["border"]),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    for i in range(len(line_items[0])):
        item_table.setStyle(TableStyle([('TEXTCOLOR', (i,0), (i,0), colors.white)]))
    elements.append(item_table)
    elements.append(Spacer(1, 8))

    # 4. Summary & Balance Table
    summary_data = [
        ["Total Taxable Solar Equipment Value:", f"₹ {base_amt:,.2f}"],
        [f"GST @ {gst_rate}% (CGST {cgst_rate}% + SGST {sgst_rate}%):", f"₹ {gst_amt:,.2f}"],
    ]
    if net_meter or transport:
        summary_data.append(["Additional Costs (Net Meter / Transport without GST):", f"₹ {(net_meter + transport):,.2f}"])

    summary_data.extend([
        ["INVOICE GRAND TOTAL:", f"₹ {total_amt:,.2f}"],
        ["Amount Received / Paid:", f"₹ {paid_amt:,.2f}"],
        ["BALANCE AMOUNT DUE:", f"₹ {balance_amt:,.2f}"]
    ])

    sum_table = Table(
        [[Paragraph(row[0], bold_body if "GRAND TOTAL" in row[0] or "BALANCE" in row[0] else body_style),
          Paragraph(f"<b>{row[1]}</b>" if "GRAND TOTAL" in row[0] or "BALANCE" in row[0] else row[1], bold_body if "GRAND TOTAL" in row[0] or "BALANCE" in row[0] else body_style)]
         for r, row in enumerate(summary_data)],
        colWidths=[380, 140]
    )
    sum_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, theme["border"]),
        ('BACKGROUND', (0,len(summary_data)-3), (-1,len(summary_data)-3), colors.HexColor("#f1f5f9")),
        ('BACKGROUND', (0,len(summary_data)-1), (-1,len(summary_data)-1), colors.HexColor("#fee2e2") if balance_amt > 0 else colors.HexColor("#dcfce7")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(sum_table)

    if is_proforma:
        elements.append(Spacer(1, 4))
        elements.append(Paragraph("<font size='7' color='#2563eb'><b>* Note:</b> This is a Proforma Invoice issued for quotation confirmation, purchase order and advance milestone payment. Formal GST Tax Invoice will be issued upon dispatch/delivery.</font>", body_style))

    elements.append(Spacer(1, 10))

    # 5. Bank Details & Signature
    bank_info = (
        f"<b>BANK PAYMENT DETAILS:</b><br/>"
        f"Account Name: <b>{company.get('company_name', 'SuryaTech Clean Energy Solutions')}</b><br/>"
        f"Bank: {company.get('bank_name', 'HDFC Bank Ltd')} | A/C No: <b>{company.get('account_no', '50200088991122')}</b><br/>"
        f"IFSC Code: <b>{company.get('ifsc_code', 'HDFC0001234')}</b> | UPI ID: <b>{company.get('upi_id', 'suryatech@hdfcbank')}</b>"
    )
    foot_data = [
        [
            Paragraph(bank_info, body_style),
            Paragraph(f"<b>For {company.get('company_name', 'SuryaTech Clean Energy Solutions')}</b><br/><br/><br/>______________________<br/>Authorized Signatory", body_style)
        ]
    ]
    foot_table = Table(foot_data, colWidths=[320, 200])
    foot_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    elements.append(foot_table)

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
