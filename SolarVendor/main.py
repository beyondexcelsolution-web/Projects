"""
Main FastAPI Web Application for Solar Vendor ERP.
Handles all REST API endpoints, PDF/Excel generation, and serves the frontend.
"""

import os
import sys
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd

from app.database import get_connection, init_db, seed_default_data
from app.calculator import calculate_solar_system, calculate_pm_surya_ghar_subsidy
from app.pdf_service import generate_quotation_pdf, generate_invoice_pdf
from app.excel_service import export_dataframe_to_excel, export_master_report
from app.trial_manager import check_trial_status, activate_license
from app.updater import (
    check_for_updates,
    start_background_download,
    get_download_progress,
    launch_installer,
    CURRENT_VERSION,
    BUILD_DATE
)

app = FastAPI(
    title="SolarPulse ERP - Generic Solar Vendor Management System",
    description="Complete Commercial & Residential Solar CRM, Engineering, DISCOM & ERP Suite",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure database is created on startup
@app.on_event("startup")
def startup():
    init_db()

# Models
class LeadCreate(BaseModel):
    name: str
    phone: str
    email: Optional[str] = ""
    address: str
    city: Optional[str] = "Bhubaneswar"
    state: Optional[str] = "Odisha"
    pincode: Optional[str] = ""
    consumer_no: Optional[str] = ""
    discom: Optional[str] = "TPCODL"
    category: Optional[str] = "Residential"
    sanctioned_load: Optional[float] = 5.0
    avg_monthly_bill: Optional[float] = 4500.0
    roof_area_sqft: Optional[float] = 600.0
    proposed_capacity_kw: Optional[float] = 5.0
    status: Optional[str] = "New"
    assigned_to: Optional[str] = "Rakesh Sharma"
    notes: Optional[str] = ""

class SurveyCreate(BaseModel):
    lead_id: int
    survey_date: Optional[str] = None
    surveyor_name: Optional[str] = "Soumya Ranjan"
    roof_type: Optional[str] = "RCC Flat"
    available_roof_area: Optional[float] = 600.0
    shadow_free_area: Optional[float] = 550.0
    azimuth_deg: Optional[float] = 180.0
    tilt_angle: Optional[float] = 20.0
    recommended_capacity_kw: Optional[float] = 5.0
    existing_connection_phase: Optional[str] = "3-Phase"
    meter_status: Optional[str] = "Single Phase Digital"
    cable_distance_dc_m: Optional[float] = 25.0
    cable_distance_ac_m: Optional[float] = 15.0
    earth_pit_space: Optional[int] = 1
    feasibility_status: Optional[str] = "Feasible"
    remarks: Optional[str] = ""

class QuoteCreate(BaseModel):
    lead_id: int
    capacity_kw: float
    panel_make: Optional[str] = "Waaree 550Wp Mono PERC Bifacial"
    panel_qty: Optional[int] = 10
    inverter_make: Optional[str] = "Growatt 5kW 3-Phase On-Grid"
    structure_type: Optional[str] = "HDG Heavy Duty Rooftop"
    bos_details: Optional[str] = "Polycab 4sqmm UV DC Cable, Type-II SPD, Dual Earthing"
    system_cost: float
    gst_rate: Optional[float] = 5.0
    gst_amount: float
    net_meter_cost: Optional[float] = 0.0
    transportation_cost: Optional[float] = 0.0
    total_project_cost: float
    subsidy_eligible: Optional[float] = 138000.0
    net_customer_cost: float
    daily_generation_kwh: Optional[float] = 13.2
    monthly_generation_kwh: Optional[float] = 396.0
    monthly_savings: Optional[float] = 2574.0
    payback_period_years: Optional[float] = 1.3
    validity_days: Optional[int] = 15
    status: Optional[str] = "Draft"

class ProjectUpdate(BaseModel):
    stage: str
    progress_pct: int
    project_manager: Optional[str] = "Amit Mohanty"
    start_date: Optional[str] = None
    target_commissioning_date: Optional[str] = None
    actual_commissioning_date: Optional[str] = None
    notes: Optional[str] = ""

class DiscomCreate(BaseModel):
    project_id: int
    lead_id: int
    discom_name: str
    division: Optional[str] = ""
    sub_division: Optional[str] = ""
    consumer_no: str
    application_ref_no: str
    applied_capacity_kw: float
    sanctioned_load_kw: float
    application_date: Optional[str] = None
    feasibility_status: Optional[str] = "Applied"
    feasibility_approval_date: Optional[str] = None
    demand_note_amount: Optional[float] = 2500.0
    demand_note_paid: Optional[int] = 1
    bi_directional_meter_no: Optional[str] = None
    meter_installed_date: Optional[str] = None
    sync_date: Optional[str] = None
    subsidy_portal_ack: Optional[str] = ""
    subsidy_status: Optional[str] = "Pending Inspection"
    subsidy_amount: Optional[float] = 138000.0

class InvoiceCreate(BaseModel):
    project_id: Optional[int] = None
    lead_id: Optional[int] = None
    invoice_type: Optional[str] = "Tax Invoice"  # "Proforma Invoice" or "Tax Invoice"
    milestone_name: str
    base_amount: float
    gst_rate: Optional[float] = 5.0
    gst_amount: float
    net_meter_cost: Optional[float] = 0.0
    transportation_cost: Optional[float] = 0.0
    total_amount: float
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[str] = "Unpaid"
    notes: Optional[str] = ""

class PaymentCreate(BaseModel):
    project_id: Optional[int] = None
    invoice_id: Optional[int] = None
    lead_id: Optional[int] = None
    transaction_type: Optional[str] = "Payment In"  # "Payment In", "Payment Out", "Project Expense"
    party_name: Optional[str] = ""
    category: Optional[str] = "Customer Collection"
    amount: float
    payment_date: str
    payment_mode: Optional[str] = "UPI"
    reference_no: Optional[str] = ""
    remarks: Optional[str] = ""

class CompanySettingsUpdate(BaseModel):
    company_name: str
    tagline: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""
    website: Optional[str] = ""
    address: Optional[str] = ""
    gstin: Optional[str] = ""
    pan: Optional[str] = ""
    bank_name: Optional[str] = ""
    account_no: Optional[str] = ""
    ifsc_code: Optional[str] = ""
    upi_id: Optional[str] = ""
    default_state: Optional[str] = "Odisha"
    default_discom: Optional[str] = "TPCODL"
    theme_color: Optional[str] = "#0f766e"

class UpdateDownloadRequest(BaseModel):
    download_url: str
    installer_name: Optional[str] = "SolarPulse_ERP_Setup_7Day_Demo.exe"
    target_version: Optional[str] = ""

class UpdateInstallRequest(BaseModel):
    silent: Optional[bool] = False


# ===================== API ENDPOINTS =====================

@app.get("/api/settings")
def get_settings():
    conn = get_connection()
    row = conn.execute("SELECT * FROM company_settings WHERE id = 1").fetchone()
    conn.close()
    if row:
        return dict(row)
    return {}

@app.post("/api/settings")
def save_settings(data: CompanySettingsUpdate):
    conn = get_connection()
    conn.execute("""
    UPDATE company_settings SET
        company_name = ?, tagline = ?, phone = ?, email = ?, website = ?,
        address = ?, gstin = ?, pan = ?, bank_name = ?, account_no = ?,
        ifsc_code = ?, upi_id = ?, default_state = ?, default_discom = ?,
        theme_color = ?
    WHERE id = 1
    """, (
        data.company_name, data.tagline, data.phone, data.email, data.website,
        data.address, data.gstin, data.pan, data.bank_name, data.account_no,
        data.ifsc_code, data.upi_id, data.default_state, data.default_discom,
        data.theme_color
    ))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Settings updated"}

@app.post("/api/reset-demo")
def reset_demo_data():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS payments")
    cursor.execute("DROP TABLE IF EXISTS invoices")
    cursor.execute("DROP TABLE IF EXISTS discom_applications")
    cursor.execute("DROP TABLE IF EXISTS projects")
    cursor.execute("DROP TABLE IF EXISTS quotations")
    cursor.execute("DROP TABLE IF EXISTS site_surveys")
    cursor.execute("DROP TABLE IF EXISTS leads")
    cursor.execute("DROP TABLE IF EXISTS company_settings")
    conn.commit()
    conn.close()

    init_db()
    return {"status": "success", "message": "Demo data reset successfully"}


@app.get("/api/dashboard")
def get_dashboard_metrics():
    conn = get_connection()
    c = conn.cursor()

    # KPI 1: Leads
    total_leads = c.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    new_leads = c.execute("SELECT COUNT(*) FROM leads WHERE status = 'New'").fetchone()[0]
    won_leads = c.execute("SELECT COUNT(*) FROM leads WHERE status = 'Won'").fetchone()[0]
    lead_conversion_rate = round((won_leads / total_leads * 100), 1) if total_leads > 0 else 0

    # KPI 2: Projects
    total_projects = c.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    commissioned_projects = c.execute("SELECT COUNT(*) FROM projects WHERE stage = 'Commissioned'").fetchone()[0]
    active_projects = total_projects - commissioned_projects

    # KPI 3: Capacity
    total_installed_kw = c.execute("SELECT COALESCE(SUM(capacity_kw), 0) FROM projects WHERE stage = 'Commissioned'").fetchone()[0]
    pipeline_kw = c.execute("SELECT COALESCE(SUM(capacity_kw), 0) FROM projects WHERE stage != 'Commissioned'").fetchone()[0]

    # KPI 4: Financials
    total_contract_value = c.execute("SELECT COALESCE(SUM(contract_value), 0) FROM projects").fetchone()[0]
    total_invoiced = c.execute("SELECT COALESCE(SUM(total_amount), 0) FROM invoices").fetchone()[0]
    total_collected = c.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE transaction_type = 'Payment In'").fetchone()[0]
    total_paid_out = c.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE transaction_type = 'Payment Out'").fetchone()[0]
    total_site_expenses = c.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE transaction_type = 'Project Expense'").fetchone()[0]
    pending_collection = max(0, total_invoiced - total_collected)

    # KPI 5: DISCOM & Subsidy
    discom_pending_count = c.execute("SELECT COUNT(*) FROM discom_applications WHERE feasibility_status != 'Commissioned'").fetchone()[0]
    subsidy_pipeline = c.execute("SELECT COALESCE(SUM(subsidy_amount), 0) FROM discom_applications WHERE subsidy_status != 'Disbursed'").fetchone()[0]

    # Charts: Monthly Trend (Simulated realistic 6 months + live DB)
    months = ["Jun 2026", "Jul 2026", "Aug 2026", "Sep 2026", "Oct 2026", "Nov 2026"]
    monthly_kw = [12.0, 18.5, 24.0, 31.0, 38.5, float(total_installed_kw + pipeline_kw)]
    monthly_revenue = [6.8, 10.2, 13.5, 17.8, 22.4, round(total_contract_value / 100000.0, 1)]

    # Charts: Funnel
    funnel = {
        "New Leads": total_leads,
        "Site Surveys": c.execute("SELECT COUNT(*) FROM site_surveys").fetchone()[0],
        "Quotations Sent": c.execute("SELECT COUNT(*) FROM quotations").fetchone()[0],
        "Projects Won": total_projects,
        "Commissioned": commissioned_projects
    }

    # Charts: DISCOM status breakdown
    discom_statuses = {}
    for row in c.execute("SELECT feasibility_status, COUNT(*) FROM discom_applications GROUP BY feasibility_status"):
        discom_statuses[row[0]] = row[1]

    # Charts: Capacity distribution
    cap_distribution = {
        "1 to 3 kW": c.execute("SELECT COUNT(*) FROM projects WHERE capacity_kw <= 3.0").fetchone()[0],
        "3.1 to 5 kW": c.execute("SELECT COUNT(*) FROM projects WHERE capacity_kw > 3.0 AND capacity_kw <= 5.0").fetchone()[0],
        "5.1 to 8 kW": c.execute("SELECT COUNT(*) FROM projects WHERE capacity_kw > 5.0 AND capacity_kw <= 8.0").fetchone()[0],
        "Above 8 kW": c.execute("SELECT COUNT(*) FROM projects WHERE capacity_kw > 8.0").fetchone()[0]
    }

    # Recent Leads
    recent_leads = [dict(r) for r in c.execute("SELECT * FROM leads ORDER BY id DESC LIMIT 5").fetchall()]

    # Active Projects List
    active_projects_list = [dict(r) for r in c.execute("""
        SELECT p.*, l.name as customer_name, l.phone, l.city
        FROM projects p
        JOIN leads l ON p.lead_id = l.id
        ORDER BY p.id DESC LIMIT 5
    """).fetchall()]

    conn.close()

    return {
        "metrics": {
            "total_leads": total_leads,
            "new_leads": new_leads,
            "won_leads": won_leads,
            "conversion_rate": lead_conversion_rate,
            "total_projects": total_projects,
            "active_projects": active_projects,
            "commissioned_projects": commissioned_projects,
            "installed_kw": total_installed_kw,
            "pipeline_kw": pipeline_kw,
            "total_contract_value": total_contract_value,
            "total_invoiced": total_invoiced,
            "total_collected": total_collected,
            "total_paid_out": total_paid_out,
            "total_site_expenses": total_site_expenses,
            "pending_collection": pending_collection,
            "discom_pending": discom_pending_count,
            "subsidy_pipeline": subsidy_pipeline
        },
        "charts": {
            "months": months,
            "monthly_kw": monthly_kw,
            "monthly_revenue_lakhs": monthly_revenue,
            "funnel": funnel,
            "discom_breakdown": discom_statuses,
            "capacity_distribution": cap_distribution
        },
        "recent_leads": recent_leads,
        "active_projects": active_projects_list
    }


# ===================== LEADS / CRM =====================

@app.get("/api/leads")
def get_leads(status: Optional[str] = None, discom: Optional[str] = None, search: Optional[str] = None):
    conn = get_connection()
    query = "SELECT * FROM leads WHERE 1=1"
    params = []

    if status and status != "All":
        query += " AND status = ?"
        params.append(status)
    if discom and discom != "All":
        query += " AND discom = ?"
        params.append(discom)
    if search:
        query += " AND (name LIKE ? OR phone LIKE ? OR consumer_no LIKE ? OR city LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term])

    query += " ORDER BY id DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/leads")
def create_lead(lead: LeadCreate):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO leads (
        name, phone, email, address, city, state, pincode,
        consumer_no, discom, category, sanctioned_load, avg_monthly_bill,
        roof_area_sqft, proposed_capacity_kw, status, assigned_to, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        lead.name, lead.phone, lead.email, lead.address, lead.city, lead.state, lead.pincode,
        lead.consumer_no, lead.discom, lead.category, lead.sanctioned_load, lead.avg_monthly_bill,
        lead.roof_area_sqft, lead.proposed_capacity_kw, lead.status, lead.assigned_to, lead.notes
    ))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"status": "success", "id": new_id, "message": "Lead created successfully"}

@app.put("/api/leads/{id}")
def update_lead(id: int, lead: LeadCreate):
    conn = get_connection()
    conn.execute("""
    UPDATE leads SET
        name = ?, phone = ?, email = ?, address = ?, city = ?, state = ?, pincode = ?,
        consumer_no = ?, discom = ?, category = ?, sanctioned_load = ?, avg_monthly_bill = ?,
        roof_area_sqft = ?, proposed_capacity_kw = ?, status = ?, assigned_to = ?, notes = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (
        lead.name, lead.phone, lead.email, lead.address, lead.city, lead.state, lead.pincode,
        lead.consumer_no, lead.discom, lead.category, lead.sanctioned_load, lead.avg_monthly_bill,
        lead.roof_area_sqft, lead.proposed_capacity_kw, lead.status, lead.assigned_to, lead.notes, id
    ))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Lead updated successfully"}

@app.delete("/api/leads/{id}")
def delete_lead(id: int):
    conn = get_connection()
    conn.execute("DELETE FROM leads WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Lead deleted"}


# ===================== SITE SURVEYS =====================

@app.get("/api/surveys")
def get_surveys():
    conn = get_connection()
    rows = conn.execute("""
        SELECT s.*, l.name as customer_name, l.phone, l.address, l.consumer_no, l.discom
        FROM site_surveys s
        JOIN leads l ON s.lead_id = l.id
        ORDER BY s.id DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/surveys")
def create_survey(survey: SurveyCreate):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO site_surveys (
        lead_id, survey_date, surveyor_name, roof_type, available_roof_area,
        shadow_free_area, azimuth_deg, tilt_angle, recommended_capacity_kw,
        existing_connection_phase, meter_status, cable_distance_dc_m, cable_distance_ac_m,
        earth_pit_space, feasibility_status, remarks
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        survey.lead_id, survey.survey_date or date.today().isoformat(), survey.surveyor_name,
        survey.roof_type, survey.available_roof_area, survey.shadow_free_area,
        survey.azimuth_deg, survey.tilt_angle, survey.recommended_capacity_kw,
        survey.existing_connection_phase, survey.meter_status, survey.cable_distance_dc_m,
        survey.cable_distance_ac_m, survey.earth_pit_space, survey.feasibility_status, survey.remarks
    ))
    # Update lead status
    cursor.execute("UPDATE leads SET status = 'Survey Scheduled' WHERE id = ? AND status = 'New'", (survey.lead_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Site survey recorded successfully"}


# ===================== CALCULATOR =====================

@app.get("/api/calculator/calculate")
def calculate_system(
    monthly_bill: Optional[float] = None,
    sanctioned_load: Optional[float] = None,
    roof_area: Optional[float] = None,
    desired_capacity: Optional[float] = None,
    tariff: Optional[float] = 6.5,
    category: Optional[str] = "Residential",
    manual_gross_cost: Optional[float] = None,
    gst_rate: Optional[float] = 5.0,
    net_meter_cost: Optional[float] = 0.0,
    transportation_cost: Optional[float] = 0.0,
    manual_subsidy: Optional[float] = None,
    units_per_day: Optional[float] = None
):
    result = calculate_solar_system(
        avg_monthly_bill=monthly_bill,
        sanctioned_load_kw=sanctioned_load,
        available_roof_area_sqft=roof_area,
        desired_capacity_kw=desired_capacity,
        tariff_per_kwh=tariff or 6.5,
        category=category or "Residential",
        manual_gross_cost=manual_gross_cost,
        gst_rate=gst_rate if gst_rate is not None else 5.0,
        net_meter_cost=net_meter_cost or 0.0,
        transportation_cost=transportation_cost or 0.0,
        manual_subsidy=manual_subsidy,
        units_per_day=units_per_day
    )
    return result


# ===================== QUOTATIONS =====================

@app.get("/api/quotations")
def get_quotations():
    conn = get_connection()
    rows = conn.execute("""
        SELECT q.*, l.name as customer_name, l.phone, l.email, l.address, l.city, l.consumer_no, l.discom, l.sanctioned_load, l.category
        FROM quotations q
        JOIN leads l ON q.lead_id = l.id
        ORDER BY q.id DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/quotations")
def create_quotation(q: QuoteCreate):
    conn = get_connection()
    cursor = conn.cursor()

    # Generate Quote Number uniquely
    max_q = cursor.execute("SELECT MAX(id) FROM quotations").fetchone()[0] or 0
    count = max_q + 1
    quote_no = f"QT-2026-{count:04d}"
    while cursor.execute("SELECT 1 FROM quotations WHERE quote_no = ?", (quote_no,)).fetchone():
        count += 1
        quote_no = f"QT-2026-{count:04d}"

    cursor.execute("""
    INSERT INTO quotations (
        quote_no, lead_id, capacity_kw, panel_make, panel_qty, inverter_make,
        structure_type, bos_details, system_cost, gst_rate, gst_amount,
        net_meter_cost, transportation_cost, total_project_cost, subsidy_eligible,
        net_customer_cost, daily_generation_kwh, monthly_generation_kwh, monthly_savings,
        payback_period_years, validity_days, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        quote_no, q.lead_id, q.capacity_kw, q.panel_make, q.panel_qty, q.inverter_make,
        q.structure_type, q.bos_details, q.system_cost, q.gst_rate or 5.0, q.gst_amount,
        q.net_meter_cost or 0.0, q.transportation_cost or 0.0,
        q.total_project_cost, q.subsidy_eligible, q.net_customer_cost,
        q.daily_generation_kwh, q.monthly_generation_kwh, q.monthly_savings,
        q.payback_period_years, q.validity_days, q.status or "Draft"
    ))

    # Update lead status
    cursor.execute("UPDATE leads SET status = 'Quoted', proposed_capacity_kw = ? WHERE id = ?", (q.capacity_kw, q.lead_id))
    conn.commit()
    conn.close()
    return {"status": "success", "quote_no": quote_no, "message": "Quotation generated successfully"}

@app.delete("/api/quotations/{id}")
def delete_quotation(id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM quotations WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Quotation deleted successfully"}

@app.post("/api/quotations/{id}/send")
def mark_quotation_sent(id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE quotations SET status = 'Sent' WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Quotation marked as Sent"}

@app.post("/api/quotations/{id}/convert-to-project")
def convert_quote_to_project(id: int):
    conn = get_connection()
    cursor = conn.cursor()

    quote = cursor.execute("SELECT * FROM quotations WHERE id = ?", (id,)).fetchone()
    if not quote:
        conn.close()
        raise HTTPException(status_code=404, detail="Quotation not found")

    lead = cursor.execute("SELECT * FROM leads WHERE id = ?", (quote['lead_id'],)).fetchone()
    consumer_no = ""
    discom = "TPCODL"
    if lead:
        try:
            consumer_no = lead['consumer_no'] or ""
            discom = lead['discom'] or "TPCODL"
        except Exception:
            pass

    # Generate Project Code uniquely
    max_p = cursor.execute("SELECT MAX(id) FROM projects").fetchone()[0] or 0
    pcount = max_p + 1
    project_code = f"PRJ-2026-{pcount:04d}"
    while cursor.execute("SELECT 1 FROM projects WHERE project_code = ?", (project_code,)).fetchone():
        pcount += 1
        project_code = f"PRJ-2026-{pcount:04d}"

    cursor.execute("""
    INSERT INTO projects (
        project_code, lead_id, quote_id, capacity_kw, contract_value, stage,
        progress_pct, project_manager, start_date, target_commissioning_date,
        consumer_no, discom, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        project_code, quote['lead_id'], quote['id'], quote['capacity_kw'], quote['total_project_cost'],
        "Order Confirmed", 15, "Amit Mohanty", date.today().isoformat(), None,
        consumer_no, discom, f"Created from quotation {quote['quote_no']}"
    ))
    new_project_id = cursor.lastrowid

    # Update quotation & lead status
    cursor.execute("UPDATE quotations SET status = 'Accepted' WHERE id = ?", (id,))
    cursor.execute("UPDATE leads SET status = 'Won' WHERE id = ?", (quote['lead_id'],))

    # Create initial Proforma Invoice for Advance Booking (15%)
    advance_base = round((quote['system_cost'] or 0.0) * 0.15, 2)
    advance_gst = round((quote['gst_amount'] or 0.0) * 0.15, 2)
    advance_net_meter = round((quote['net_meter_cost'] or 0.0) * 0.15, 2)
    advance_transport = round((quote['transportation_cost'] or 0.0) * 0.15, 2)
    advance_total = round((quote['total_project_cost'] or 0.0) * 0.15, 2)

    max_inv = cursor.execute("SELECT MAX(id) FROM invoices").fetchone()[0] or 0
    inv_count = max_inv + 1
    inv_no = f"PI-2026-{inv_count:04d}"
    while cursor.execute("SELECT 1 FROM invoices WHERE invoice_no = ?", (inv_no,)).fetchone():
        inv_count += 1
        inv_no = f"PI-2026-{inv_count:04d}"

    cursor.execute("""
    INSERT INTO invoices (
        invoice_no, project_id, lead_id, invoice_type, milestone_name,
        base_amount, gst_rate, gst_amount, net_meter_cost, transportation_cost,
        total_amount, invoice_date, due_date, status, paid_amount, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        inv_no, new_project_id, quote['lead_id'], "Proforma Invoice", "Advance Booking (15%)",
        advance_base, quote['gst_rate'] or 5.0, advance_gst, advance_net_meter, advance_transport,
        advance_total, date.today().isoformat(), None, "Unpaid", 0.0,
        f"Advance Proforma on order booking (Quote {quote['quote_no']})"
    ))

    conn.commit()
    conn.close()
    return {"status": "success", "project_code": project_code, "project_id": new_project_id, "invoice_no": inv_no}

    conn.commit()
    conn.close()
    return {"status": "success", "project_code": project_code, "project_id": new_project_id, "invoice_no": inv_no}


# ===================== PROJECTS & INSTALLATION =====================

@app.get("/api/projects")
def get_projects(stage: Optional[str] = None):
    conn = get_connection()
    query = """
        SELECT p.*, l.name as customer_name, l.phone, l.email, l.address, l.city, l.pincode, l.sanctioned_load, l.category,
               COALESCE(SUM(pay.amount), 0) as total_paid
        FROM projects p
        JOIN leads l ON p.lead_id = l.id
        LEFT JOIN payments pay ON pay.project_id = p.id
        WHERE 1=1
    """
    params = []
    if stage and stage != "All":
        query += " AND p.stage = ?"
        params.append(stage)

    query += " GROUP BY p.id ORDER BY p.id DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.put("/api/projects/{id}/stage")
def update_project_stage(id: int, p: ProjectUpdate):
    conn = get_connection()
    conn.execute("""
    UPDATE projects SET
        stage = ?, progress_pct = ?, project_manager = ?,
        start_date = COALESCE(?, start_date),
        target_commissioning_date = COALESCE(?, target_commissioning_date),
        actual_commissioning_date = COALESCE(?, actual_commissioning_date),
        notes = ?
    WHERE id = ?
    """, (
        p.stage, p.progress_pct, p.project_manager, p.start_date,
        p.target_commissioning_date, p.actual_commissioning_date, p.notes, id
    ))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Project milestone updated"}


# ===================== DISCOM & NET METERING =====================

@app.get("/api/discom")
def get_discom_applications():
    conn = get_connection()
    rows = conn.execute("""
        SELECT d.*, l.name as customer_name, l.phone, l.address, l.city, p.project_code, p.stage as project_stage
        FROM discom_applications d
        JOIN leads l ON d.lead_id = l.id
        JOIN projects p ON d.project_id = p.id
        ORDER BY d.id DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/discom")
def create_discom_app(d: DiscomCreate):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO discom_applications (
        project_id, lead_id, discom_name, division, sub_division,
        consumer_no, application_ref_no, applied_capacity_kw, sanctioned_load_kw,
        application_date, feasibility_status, feasibility_approval_date,
        demand_note_amount, demand_note_paid, bi_directional_meter_no,
        meter_installed_date, sync_date, subsidy_portal_ack,
        subsidy_status, subsidy_amount
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        d.project_id, d.lead_id, d.discom_name, d.division, d.sub_division,
        d.consumer_no, d.application_ref_no, d.applied_capacity_kw, d.sanctioned_load_kw,
        d.application_date or date.today().isoformat(), d.feasibility_status, d.feasibility_approval_date,
        d.demand_note_amount, d.demand_note_paid, d.bi_directional_meter_no,
        d.meter_installed_date, d.sync_date, d.subsidy_portal_ack,
        d.subsidy_status, d.subsidy_amount
    ))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "DISCOM application logged"}

@app.put("/api/discom/{id}")
def update_discom_status(id: int, status: str, meter_no: Optional[str] = None):
    conn = get_connection()
    conn.execute("""
    UPDATE discom_applications SET
        feasibility_status = ?,
        bi_directional_meter_no = COALESCE(?, bi_directional_meter_no)
    WHERE id = ?
    """, (status, meter_no, id))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "DISCOM application status updated"}


# ===================== INVOICING & BILLING =====================

@app.get("/api/invoices")
def get_invoices(invoice_type: Optional[str] = None):
    conn = get_connection()
    query = """
        SELECT i.*, 
               COALESCE(l.name, 'Direct Client') as customer_name,
               COALESCE(l.phone, '') as phone,
               COALESCE(l.address, '') as address,
               COALESCE(l.city, '') as city,
               COALESCE(l.consumer_no, '') as consumer_no,
               COALESCE(l.discom, 'TPCODL') as discom,
               COALESCE(p.project_code, 'N/A') as project_code,
               COALESCE(p.capacity_kw, 0.0) as capacity_kw
        FROM invoices i
        LEFT JOIN leads l ON i.lead_id = l.id
        LEFT JOIN projects p ON i.project_id = p.id
        WHERE 1=1
    """
    params = []
    if invoice_type and invoice_type != "All":
        query += " AND i.invoice_type = ?"
        params.append(invoice_type)

    query += " ORDER BY i.id DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/invoices")
def create_invoice(inv: InvoiceCreate):
    conn = get_connection()
    cursor = conn.cursor()
    
    max_inv = cursor.execute("SELECT MAX(id) FROM invoices").fetchone()[0] or 0
    count = max_inv + 1
    prefix = "PI" if inv.invoice_type == "Proforma Invoice" else "INV"
    invoice_no = f"{prefix}-2026-{count:04d}"
    while cursor.execute("SELECT 1 FROM invoices WHERE invoice_no = ?", (invoice_no,)).fetchone():
        count += 1
        invoice_no = f"{prefix}-2026-{count:04d}"

    lead_id = inv.lead_id
    if not lead_id and inv.project_id:
        p_row = cursor.execute("SELECT lead_id FROM projects WHERE id = ?", (inv.project_id,)).fetchone()
        if p_row:
            lead_id = p_row[0]
    if not lead_id:
        first_lead = cursor.execute("SELECT id FROM leads LIMIT 1").fetchone()
        lead_id = first_lead[0] if first_lead else 1

    project_id = inv.project_id or 1

    cursor.execute("""
    INSERT INTO invoices (
        invoice_no, project_id, lead_id, invoice_type, milestone_name,
        base_amount, gst_rate, gst_amount, net_meter_cost, transportation_cost,
        total_amount, invoice_date, due_date, status, paid_amount, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        invoice_no, project_id, lead_id, inv.invoice_type or "Tax Invoice", inv.milestone_name,
        inv.base_amount, inv.gst_rate or 5.0, inv.gst_amount, inv.net_meter_cost or 0.0,
        inv.transportation_cost or 0.0, inv.total_amount,
        inv.invoice_date or date.today().isoformat(), inv.due_date,
        inv.status or "Unpaid", 0.0, inv.notes
    ))
    conn.commit()
    conn.close()
    return {"status": "success", "invoice_no": invoice_no, "message": f"{inv.invoice_type} generated successfully"}

@app.post("/api/invoices/{id}/convert-to-tax-invoice")
def convert_to_tax_invoice(id: int):
    conn = get_connection()
    cursor = conn.cursor()
    inv = cursor.execute("SELECT * FROM invoices WHERE id = ?", (id,)).fetchone()
    if not inv:
        conn.close()
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Generate new Tax Invoice number
    max_inv = cursor.execute("SELECT MAX(id) FROM invoices").fetchone()[0] or 0
    icount = max_inv + 1
    new_inv_no = f"INV-2026-{icount:04d}"
    while cursor.execute("SELECT 1 FROM invoices WHERE invoice_no = ?", (new_inv_no,)).fetchone():
        icount += 1
        new_inv_no = f"INV-2026-{icount:04d}"

    old_notes = inv['notes'] or ''
    new_notes = f"{old_notes} (Converted from Proforma {inv['invoice_no']})".strip()

    cursor.execute("""
    UPDATE invoices SET
        invoice_type = 'Tax Invoice',
        invoice_no = ?,
        notes = ?
    WHERE id = ?
    """, (new_inv_no, new_notes, id))
    conn.commit()
    conn.close()
    return {"status": "success", "new_invoice_no": new_inv_no, "message": "Proforma converted to Tax Invoice successfully"}

@app.delete("/api/invoices/{id}")
def delete_invoice(id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM invoices WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Invoice deleted successfully"}


# ===================== PAYMENTS LEDGER =====================

@app.get("/api/payments/summary")
def get_payment_summary():
    conn = get_connection()
    c = conn.cursor()
    total_in = c.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE transaction_type = 'Payment In'").fetchone()[0]
    total_out = c.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE transaction_type = 'Payment Out'").fetchone()[0]
    total_expenses = c.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE transaction_type = 'Project Expense'").fetchone()[0]
    net_cashflow = total_in - (total_out + total_expenses)
    conn.close()
    return {
        "total_in": round(float(total_in), 2),
        "total_out": round(float(total_out), 2),
        "total_expenses": round(float(total_expenses), 2),
        "net_cashflow": round(float(net_cashflow), 2)
    }

@app.get("/api/payments")
def get_payments(transaction_type: Optional[str] = None):
    conn = get_connection()
    query = """
        SELECT pay.*, 
               COALESCE(NULLIF(pay.party_name, ''), l.name, 'Direct Client') as display_party,
               l.name as customer_name, l.phone, 
               p.project_code, p.capacity_kw, 
               i.invoice_no
        FROM payments pay
        LEFT JOIN leads l ON pay.lead_id = l.id
        LEFT JOIN projects p ON pay.project_id = p.id
        LEFT JOIN invoices i ON pay.invoice_id = i.id
        WHERE 1=1
    """
    params = []
    if transaction_type and transaction_type != "All":
        query += " AND pay.transaction_type = ?"
        params.append(transaction_type)

    query += " ORDER BY pay.id DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/payments")
def record_payment(pay: PaymentCreate):
    conn = get_connection()
    cursor = conn.cursor()
    max_pay = cursor.execute("SELECT MAX(id) FROM payments").fetchone()[0] or 0
    count = max_pay + 1

    trans_type = pay.transaction_type or "Payment In"
    if trans_type == "Payment Out":
        prefix = "VOU"
    elif trans_type == "Project Expense":
        prefix = "EXP"
    else:
        prefix = "RCT"

    receipt_no = f"{prefix}-2026-{count:04d}"
    while cursor.execute("SELECT 1 FROM payments WHERE receipt_no = ?", (receipt_no,)).fetchone():
        count += 1
        receipt_no = f"{prefix}-2026-{count:04d}"

    lead_id = pay.lead_id
    if not lead_id and pay.project_id:
        p_row = cursor.execute("SELECT lead_id FROM projects WHERE id = ?", (pay.project_id,)).fetchone()
        if p_row:
            lead_id = p_row[0]

    party_name = pay.party_name or ""
    if not party_name and lead_id:
        l_row = cursor.execute("SELECT name FROM leads WHERE id = ?", (lead_id,)).fetchone()
        if l_row:
            party_name = l_row[0]

    if not lead_id:
        first_lead = cursor.execute("SELECT id FROM leads LIMIT 1").fetchone()
        lead_id = first_lead[0] if first_lead else 1

    cursor.execute("""
    INSERT INTO payments (
        receipt_no, project_id, invoice_id, lead_id, transaction_type,
        party_name, category, amount, payment_date, payment_mode,
        reference_no, status, remarks
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Verified', ?)
    """, (
        receipt_no, pay.project_id, pay.invoice_id, lead_id, trans_type,
        party_name, pay.category or "General", pay.amount,
        pay.payment_date, pay.payment_mode, pay.reference_no, pay.remarks
    ))

    # Update invoice paid amount & status if linked and Payment In
    if pay.invoice_id and trans_type == "Payment In":
        cursor.execute("""
        UPDATE invoices SET
            paid_amount = paid_amount + ?,
            status = CASE
                WHEN paid_amount + ? >= total_amount THEN 'Paid'
                ELSE 'Partially Paid'
            END
        WHERE id = ?
        """, (pay.amount, pay.amount, pay.invoice_id))

    conn.commit()
    conn.close()
    return {"status": "success", "receipt_no": receipt_no, "message": f"{trans_type} recorded successfully"}

@app.delete("/api/payments/{id}")
def delete_payment(id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM payments WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Payment record deleted"}


# ===================== PDF GENERATION ENDPOINTS =====================

@app.get("/api/pdf/quotation/{id}")
def download_quotation_pdf(id: int):
    conn = get_connection()
    quote = conn.execute("""
        SELECT q.*, l.name as customer_name, l.phone, l.email, l.address, l.city, l.consumer_no, l.discom, l.sanctioned_load, l.category
        FROM quotations q
        JOIN leads l ON q.lead_id = l.id
        WHERE q.id = ?
    """, (id,)).fetchone()

    company = conn.execute("SELECT * FROM company_settings WHERE id = 1").fetchone()
    conn.close()

    if not quote:
        raise HTTPException(status_code=404, detail="Quotation not found")

    pdf_bytes = generate_quotation_pdf(dict(quote), dict(company) if company else {})
    filename = f"Quotation_{quote['quote_no']}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'}
    )

@app.get("/api/pdf/invoice/{id}")
def download_invoice_pdf(id: int):
    conn = get_connection()
    inv = conn.execute("""
        SELECT i.*, l.name as customer_name, l.phone, l.address, l.city, l.consumer_no, l.discom,
               p.project_code, p.capacity_kw
        FROM invoices i
        JOIN leads l ON i.lead_id = l.id
        JOIN projects p ON i.project_id = p.id
        WHERE i.id = ?
    """, (id,)).fetchone()

    company = conn.execute("SELECT * FROM company_settings WHERE id = 1").fetchone()
    conn.close()

    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    pdf_bytes = generate_invoice_pdf(dict(inv), dict(company) if company else {})
    filename = f"Invoice_{inv['invoice_no']}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'}
    )


# ===================== EXCEL EXPORT ENDPOINTS =====================

@app.get("/api/export/excel/{data_type}")
def export_excel(data_type: str):
    conn = get_connection()

    if data_type == "leads":
        df = pd.read_sql_query("SELECT id, name, phone, email, city, consumer_no, discom, category, sanctioned_load, proposed_capacity_kw, status, assigned_to, created_at FROM leads ORDER BY id DESC", conn)
        filename = "Solar_Leads_Report.xlsx"
        sheet_name = "Leads"
        excel_bytes = export_dataframe_to_excel(df, sheet_name)

    elif data_type == "projects":
        df = pd.read_sql_query("""
            SELECT p.project_code, l.name as customer_name, l.phone, p.capacity_kw, p.contract_value, p.stage, p.progress_pct, p.discom, p.consumer_no, p.start_date, p.target_commissioning_date
            FROM projects p
            JOIN leads l ON p.lead_id = l.id
            ORDER BY p.id DESC
        """, conn)
        filename = "Solar_Projects_Pipeline.xlsx"
        sheet_name = "Projects"
        excel_bytes = export_dataframe_to_excel(df, sheet_name)

    elif data_type == "invoices":
        df = pd.read_sql_query("""
            SELECT i.invoice_no, i.invoice_type, COALESCE(p.project_code, 'N/A') as project_code, 
                   COALESCE(l.name, 'Direct Client') as customer_name, i.milestone_name, 
                   i.base_amount, i.gst_amount, i.net_meter_cost, i.transportation_cost, 
                   i.total_amount, i.paid_amount, i.status, i.invoice_date, i.due_date
            FROM invoices i
            LEFT JOIN leads l ON i.lead_id = l.id
            LEFT JOIN projects p ON i.project_id = p.id
            ORDER BY i.id DESC
        """, conn)
        filename = "Solar_Billing_Invoices.xlsx"
        sheet_name = "Invoices"
        excel_bytes = export_dataframe_to_excel(df, sheet_name)

    elif data_type == "discom":
        df = pd.read_sql_query("""
            SELECT d.application_ref_no, p.project_code, l.name as customer_name, d.discom_name, d.consumer_no, d.applied_capacity_kw, d.sanctioned_load_kw, d.feasibility_status, d.bi_directional_meter_no, d.subsidy_status, d.subsidy_amount
            FROM discom_applications d
            JOIN leads l ON d.lead_id = l.id
            JOIN projects p ON d.project_id = p.id
            ORDER BY d.id DESC
        """, conn)
        filename = "DISCOM_Net_Metering_Report.xlsx"
        sheet_name = "DISCOM"
        excel_bytes = export_dataframe_to_excel(df, sheet_name)

    elif data_type == "payments":
        df = pd.read_sql_query("""
            SELECT pay.receipt_no, pay.transaction_type, 
                   COALESCE(NULLIF(pay.party_name, ''), l.name, 'Direct') as party_name,
                   pay.category, COALESCE(p.project_code, 'N/A') as project_code, 
                   pay.amount, pay.payment_date, pay.payment_mode, pay.reference_no, pay.status
            FROM payments pay
            LEFT JOIN leads l ON pay.lead_id = l.id
            LEFT JOIN projects p ON pay.project_id = p.id
            ORDER BY pay.id DESC
        """, conn)
        filename = "Solar_Payments_Ledger.xlsx"
        sheet_name = "Payments"
        excel_bytes = export_dataframe_to_excel(df, sheet_name)

    elif data_type == "master":
        leads_df = pd.read_sql_query("SELECT * FROM leads", conn)
        projects_df = pd.read_sql_query("SELECT * FROM projects", conn)
        quotes_df = pd.read_sql_query("SELECT * FROM quotations", conn)
        discom_df = pd.read_sql_query("SELECT * FROM discom_applications", conn)
        inv_df = pd.read_sql_query("SELECT * FROM invoices", conn)
        pay_df = pd.read_sql_query("SELECT * FROM payments", conn)

        tables = {
            "Leads Summary": leads_df,
            "Projects Tracking": projects_df,
            "Quotations": quotes_df,
            "DISCOM & Net Meter": discom_df,
            "Invoices": inv_df,
            "Payments Ledger": pay_df
        }
        filename = "Solar_Vendor_Master_ERP_Report.xlsx"
        excel_bytes = export_master_report(tables)
    else:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid report type")

    conn.close()
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# Serve Static UI files
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

static_dir = os.path.join(base_path, "app", "static")
if not os.path.exists(static_dir):
    # fallback to local app/static next to executable
    static_dir = os.path.join(os.path.dirname(sys.executable), "app", "static")
    if not os.path.exists(static_dir):
        os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/api/trial-status")
def get_trial_status():
    return check_trial_status()

class LicenseActivateRequest(BaseModel):
    key: str

@app.post("/api/activate-license")
def activate_app_license(req: LicenseActivateRequest):
    success = activate_license(req.key)
    if success:
        return {"status": "success", "message": "SolarPulse ERP Full Lifetime License Activated Successfully!"}
    raise HTTPException(status_code=400, detail="Invalid Activation Key. Please contact vendor.")


# ===================== SOFTWARE UPDATE ENDPOINTS =====================

@app.get("/api/update/check")
def check_update_status():
    return check_for_updates()

@app.post("/api/update/download")
def download_update_package(req: UpdateDownloadRequest):
    return start_background_download(req.download_url, req.installer_name, req.target_version or "")

@app.get("/api/update/progress")
def get_update_download_progress():
    return get_download_progress()

@app.post("/api/update/install")
def install_update_package(req: UpdateInstallRequest):
    return launch_installer(silent=bool(req.silent))

def render_trial_expired_html(trial_info):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SolarPulse ERP - 7-Day Demo Expired</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/lucide@latest"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex items-center justify-center p-4 font-sans">
  <div class="max-w-lg w-full bg-slate-900 border border-amber-500/30 rounded-2xl p-8 shadow-2xl relative overflow-hidden">
    <!-- Glow accent -->
    <div class="absolute -top-24 -right-24 w-48 h-48 bg-amber-500/10 rounded-full blur-3xl pointer-events-none"></div>
    <div class="absolute -bottom-24 -left-24 w-48 h-48 bg-teal-500/10 rounded-full blur-3xl pointer-events-none"></div>

    <div class="text-center space-y-4">
      <div class="w-16 h-16 bg-gradient-to-tr from-amber-500 to-amber-600 rounded-2xl mx-auto flex items-center justify-center shadow-lg shadow-amber-500/20">
        <i data-lucide="lock" class="w-8 h-8 text-slate-950"></i>
      </div>
      
      <div>
        <span class="bg-amber-500/20 text-amber-300 text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider border border-amber-500/30">7-Day Demo Period Concluded</span>
        <h1 class="text-2xl font-black text-white mt-2">Evaluation Trial Expired</h1>
        <p class="text-xs text-slate-400 mt-1">First Installed: <b>{trial_info.get('first_run_str', 'N/A')}</b> • Expired On: <b>{trial_info.get('expires_str', 'N/A')}</b></p>
      </div>

      <div class="bg-slate-800/80 border border-slate-700/80 rounded-xl p-4 text-left text-xs space-y-2">
        <p class="text-slate-300">
          Aapka <b>7-din ka demo evaluation trial</b> complete ho chuka hai. Is Solar Vendor ERP & CRM system ko aage use karne ya <b>Full Lifetime Commercial License</b> khareedne ke liye sampark karein:
        </p>
        <div class="pt-2 border-t border-slate-700/80 space-y-1 text-slate-200">
          <div class="flex items-center space-x-2">
            <i data-lucide="phone" class="w-3.5 h-3.5 text-amber-400"></i>
            <span>Official Helpline: <b>+91 90000 00000</b></span>
          </div>
          <div class="flex items-center space-x-2">
            <i data-lucide="mail" class="w-3.5 h-3.5 text-amber-400"></i>
            <span>Email: <b>sales@suryatechenergy.com</b></span>
          </div>
          <div class="flex items-center space-x-2">
            <i data-lucide="map-pin" class="w-3.5 h-3.5 text-amber-400"></i>
            <span>Bhubaneswar, Odisha - India</span>
          </div>
        </div>
      </div>

      <!-- License Activation Form -->
      <div class="pt-2 text-left space-y-2">
        <label class="block text-xs font-semibold text-slate-300">Have an Activation License Key?</label>
        <div class="flex space-x-2">
          <input type="text" id="activationKeyInput" placeholder="SOLARPULSE-XXXX-XXXX" 
                 class="flex-1 bg-slate-800 border border-slate-700 text-white font-mono text-xs px-3 py-2.5 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 uppercase">
          <button onclick="submitActivation()" 
                  class="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold px-4 py-2.5 text-xs rounded-lg transition shadow-md">
            Activate
          </button>
        </div>
        <div id="activationResult" class="text-xs font-semibold hidden"></div>
      </div>
    </div>
  </div>

  <script>
    lucide.createIcons();
    async function submitActivation() {{
      const key = document.getElementById('activationKeyInput').value.trim();
      const resEl = document.getElementById('activationResult');
      if (!key) return;

      try {{
        const resp = await fetch('/api/activate-license', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ key: key }})
        }});
        const data = await resp.json();
        if (resp.ok) {{
          resEl.className = 'text-xs font-bold text-emerald-400 block';
          resEl.innerText = data.message;
          setTimeout(() => window.location.reload(), 1500);
        }} else {{
          resEl.className = 'text-xs font-bold text-red-400 block';
          resEl.innerText = data.detail || 'Invalid Key';
        }}
      }} catch (e) {{
        resEl.className = 'text-xs font-bold text-red-400 block';
        resEl.innerText = 'Activation error. Check network or key.';
      }}
    }}
  </script>
</body>
</html>"""

@app.get("/")
def serve_index():
    # Check 7-day trial status
    trial = check_trial_status()
    if trial.get("is_expired"):
        return HTMLResponse(render_trial_expired_html(trial))

    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>Solar Vendor ERP Backend Ready. Index page loading...</h1>")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
