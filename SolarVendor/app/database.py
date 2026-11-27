"""
Database configuration and initial data seeding for Solar Vendor ERP.
Uses SQLite for zero-configuration, blazingly fast local storage.
"""

import sqlite3
import os
import sys
import json
from datetime import datetime, date

if getattr(sys, 'frozen', False):
    appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
    data_dir = os.path.join(appdata, "SolarPulseERP")
    os.makedirs(data_dir, exist_ok=True)
    DB_PATH = os.path.join(data_dir, "solar_vendor.db")
else:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "solar_vendor.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Company Settings / Vendor Profile (White-Label)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS company_settings (
        id INTEGER PRIMARY KEY,
        company_name TEXT NOT NULL,
        tagline TEXT,
        logo_url TEXT,
        phone TEXT,
        email TEXT,
        website TEXT,
        address TEXT,
        gstin TEXT,
        pan TEXT,
        bank_name TEXT,
        account_no TEXT,
        ifsc_code TEXT,
        upi_id TEXT,
        default_state TEXT,
        default_discom TEXT,
        theme_color TEXT
    )
    """)

    # 2. Leads / Customers
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT,
        address TEXT NOT NULL,
        city TEXT,
        state TEXT DEFAULT 'Odisha',
        pincode TEXT,
        consumer_no TEXT,
        discom TEXT DEFAULT 'TPCODL',
        category TEXT DEFAULT 'Residential',
        sanctioned_load REAL DEFAULT 5.0,
        avg_monthly_bill REAL DEFAULT 4500.0,
        roof_area_sqft REAL DEFAULT 600.0,
        proposed_capacity_kw REAL DEFAULT 5.0,
        status TEXT DEFAULT 'New', -- New, Contacted, Survey Scheduled, Quoted, Won, Lost
        assigned_to TEXT DEFAULT 'Rakesh Sharma',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 3. Site Surveys
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS site_surveys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER NOT NULL,
        survey_date DATE,
        surveyor_name TEXT,
        roof_type TEXT DEFAULT 'RCC Flat',
        available_roof_area REAL,
        shadow_free_area REAL,
        azimuth_deg REAL DEFAULT 180.0,
        tilt_angle REAL DEFAULT 20.0,
        recommended_capacity_kw REAL,
        existing_connection_phase TEXT DEFAULT '3-Phase',
        meter_status TEXT DEFAULT 'Single Phase Digital',
        cable_distance_dc_m REAL DEFAULT 25.0,
        cable_distance_ac_m REAL DEFAULT 15.0,
        earth_pit_space INTEGER DEFAULT 1,
        feasibility_status TEXT DEFAULT 'Feasible',
        remarks TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(lead_id) REFERENCES leads(id) ON DELETE CASCADE
    )
    """)

    # 4. Quotations
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quotations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quote_no TEXT UNIQUE NOT NULL,
        lead_id INTEGER NOT NULL,
        capacity_kw REAL NOT NULL,
        panel_make TEXT DEFAULT 'Waaree 550Wp Mono PERC Bifacial',
        panel_qty INTEGER DEFAULT 10,
        inverter_make TEXT DEFAULT 'Growatt 5kW 3-Phase On-Grid',
        structure_type TEXT DEFAULT 'HDG Heavy Duty Rooftop',
        bos_details TEXT,
        system_cost REAL NOT NULL,
        gst_rate REAL DEFAULT 5.0,
        gst_amount REAL NOT NULL,
        net_meter_cost REAL DEFAULT 3500.0,
        transportation_cost REAL DEFAULT 2500.0,
        total_project_cost REAL NOT NULL,
        subsidy_eligible REAL DEFAULT 138000.0,
        net_customer_cost REAL NOT NULL,
        daily_generation_kwh REAL DEFAULT 13.8,
        monthly_generation_kwh REAL NOT NULL,
        monthly_savings REAL NOT NULL,
        payback_period_years REAL NOT NULL,
        validity_days INTEGER DEFAULT 15,
        status TEXT DEFAULT 'Draft',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(lead_id) REFERENCES leads(id) ON DELETE CASCADE
    )
    """)

    # 5. Projects
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_code TEXT UNIQUE NOT NULL,
        lead_id INTEGER NOT NULL,
        quote_id INTEGER,
        capacity_kw REAL NOT NULL,
        contract_value REAL NOT NULL,
        stage TEXT DEFAULT 'Order Confirmed',
        progress_pct INTEGER DEFAULT 15,
        project_manager TEXT DEFAULT 'Amit Mohanty',
        start_date DATE,
        target_commissioning_date DATE,
        actual_commissioning_date DATE,
        consumer_no TEXT,
        discom TEXT DEFAULT 'TPCODL',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(lead_id) REFERENCES leads(id) ON DELETE CASCADE,
        FOREIGN KEY(quote_id) REFERENCES quotations(id) ON DELETE SET NULL
    )
    """)

    # 6. DISCOM & Net Metering Applications
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS discom_applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        lead_id INTEGER NOT NULL,
        discom_name TEXT NOT NULL,
        division TEXT,
        sub_division TEXT,
        consumer_no TEXT NOT NULL,
        application_ref_no TEXT UNIQUE NOT NULL,
        applied_capacity_kw REAL NOT NULL,
        sanctioned_load_kw REAL NOT NULL,
        application_date DATE,
        feasibility_status TEXT DEFAULT 'Applied',
        feasibility_approval_date DATE,
        demand_note_amount REAL DEFAULT 2500.0,
        demand_note_paid INTEGER DEFAULT 1,
        bi_directional_meter_no TEXT,
        meter_installed_date DATE,
        sync_date DATE,
        subsidy_portal_ack TEXT,
        subsidy_status TEXT DEFAULT 'Pending Inspection',
        subsidy_amount REAL DEFAULT 138000.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY(lead_id) REFERENCES leads(id) ON DELETE CASCADE
    )
    """)

    # 7. Invoices & Billing (Proforma Invoice vs Tax Invoice)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_no TEXT UNIQUE NOT NULL,
        project_id INTEGER NOT NULL,
        lead_id INTEGER NOT NULL,
        invoice_type TEXT DEFAULT 'Tax Invoice', -- Proforma Invoice, Tax Invoice
        milestone_name TEXT DEFAULT 'Advance Booking (15%)',
        base_amount REAL NOT NULL,
        gst_rate REAL DEFAULT 5.0,
        gst_amount REAL NOT NULL,
        net_meter_cost REAL DEFAULT 0.0,
        transportation_cost REAL DEFAULT 0.0,
        total_amount REAL NOT NULL,
        invoice_date DATE,
        due_date DATE,
        status TEXT DEFAULT 'Unpaid',
        paid_amount REAL DEFAULT 0.0,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY(lead_id) REFERENCES leads(id) ON DELETE CASCADE
    )
    """)

    # 8. Payments Ledger (Payment In, Payment Out, Project Expenses)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        receipt_no TEXT UNIQUE NOT NULL,
        transaction_type TEXT DEFAULT 'Payment In', -- 'Payment In', 'Payment Out', 'Project Expense'
        party_name TEXT DEFAULT '',
        category TEXT DEFAULT 'Customer Collection', -- Customer Collection, Modules & Inverters, Structure & Fabrication, Electrical & BoS, Site Labor & Civil, Transportation, DISCOM Liaisoning, Misc
        project_id INTEGER,
        invoice_id INTEGER,
        lead_id INTEGER,
        amount REAL NOT NULL,
        payment_date DATE NOT NULL,
        payment_mode TEXT DEFAULT 'UPI',
        reference_no TEXT,
        status TEXT DEFAULT 'Verified',
        remarks TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE SET NULL,
        FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE SET NULL,
        FOREIGN KEY(lead_id) REFERENCES leads(id) ON DELETE SET NULL
    )
    """)

    # Run auto-migrations for existing databases
    def add_col_if_missing(table, col_def):
        col_name = col_def.split()[0]
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")
        except Exception:
            pass

    add_col_if_missing("quotations", "net_meter_cost REAL DEFAULT 0.0")
    add_col_if_missing("quotations", "transportation_cost REAL DEFAULT 0.0")
    add_col_if_missing("quotations", "daily_generation_kwh REAL DEFAULT 13.8")

    add_col_if_missing("invoices", "net_meter_cost REAL DEFAULT 0.0")
    add_col_if_missing("invoices", "transportation_cost REAL DEFAULT 0.0")

    add_col_if_missing("payments", "transaction_type TEXT DEFAULT 'Payment In'")
    add_col_if_missing("payments", "party_name TEXT DEFAULT ''")
    add_col_if_missing("payments", "category TEXT DEFAULT 'Customer Collection'")

    conn.commit()
    seed_default_data(conn)
    conn.close()

def seed_default_data(conn):
    cursor = conn.cursor()

    # Check if company settings exist
    cursor.execute("SELECT COUNT(*) FROM company_settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO company_settings (
            id, company_name, tagline, phone, email, website,
            address, gstin, pan, bank_name, account_no, ifsc_code, upi_id,
            default_state, default_discom, theme_color
        ) VALUES (
            1,
            'SuryaTech Clean Energy Solutions',
            'Empowering Homes & Businesses with Smart Rooftop Solar',
            '+91 90000 00000',
            'sales@suryatechenergy.com',
            'www.suryatechenergy.com',
            'Plot No. 402, Saheed Nagar, Bhubaneswar, Odisha - 751007',
            '21AAECS9876Q1Z8',
            'AAECS9876Q',
            'HDFC Bank Ltd, Saheed Nagar Branch',
            '50200088991122',
            'HDFC0001234',
            'suryatech@hdfcbank',
            'Odisha',
            'TPCODL',
            '#059669'
        )
        """)

    # Check if leads exist
    cursor.execute("SELECT COUNT(*) FROM leads")
    if cursor.fetchone()[0] == 0:
        initial_leads = [
            (
                "Subrat Kumar Jena", "+91 90000 00001", "subrat.jena@example.com",
                "Plot 214, Patia, Near KIIT Square", "Bhubaneswar", "Odisha", "751024",
                "01A2345678", "TPCODL", "Residential", 5.0, 4800.0, 650.0, 5.0,
                "Quoted", "Rakesh Sharma", "Looking for 5kW Mono PERC with PM Surya Ghar subsidy."
            ),
            (
                "Debashish Pattnaik", "+91 90000 00002", "debashish.p@example.com",
                "HIG-45, Phase 2, Chandrasekharpur", "Bhubaneswar", "Odisha", "751016",
                "01B9876543", "TPCODL", "Residential", 3.0, 2900.0, 450.0, 3.0,
                "Won", "Priya Das", "High priority, token paid, site survey completed."
            ),
            (
                "Manoj Kumar Sahoo", "+91 90000 00003", "manoj.sahoo@example.com",
                "Station Road, Near Railway Colony", "Cuttack", "Odisha", "753003",
                "02C4567891", "TPCODL", "Residential", 8.0, 7200.0, 950.0, 8.0,
                "Won", "Rakesh Sharma", "Installation underway. 8kW high rise structure."
            ),
            (
                "Kishore Chandra Das", "+91 90000 00004", "kcdas.balasore@example.com",
                "Remuna Golei, Main Highway Road", "Balasore", "Odisha", "756001",
                "03D6789012", "TPNODL", "Residential", 4.0, 3800.0, 520.0, 4.0,
                "Survey Scheduled", "Amit Mohanty", "Survey assigned for Friday."
            ),
            (
                "Suresh Agrawal", "+91 90000 00005", "suresh.sambalpur@example.com",
                "Budharaja Road, Near Golbazar", "Sambalpur", "Odisha", "768004",
                "04E1122334", "TPWODL", "Residential", 10.0, 9500.0, 1200.0, 10.0,
                "Quoted", "Priya Das", "Commercial cum residential bungalow rooftop."
            ),
            (
                "Dr. Niranjan Behera", "+91 90000 00006", "dr.niranjan@example.com",
                "Brahma Nagar 3rd Line", "Berhampur", "Odisha", "760001",
                "05F5566778", "TPSODL", "Residential", 6.0, 5600.0, 750.0, 6.0,
                "Won", "Rakesh Sharma", "Commissioned last week, subsidy application logged."
            ),
            (
                "Pramod Tripathy", "+91 90000 00007", "pramod.trip@example.com",
                "Jayadev Vihar, IRC Village", "Bhubaneswar", "Odisha", "751015",
                "01A7788990", "TPCODL", "Residential", 3.0, 3100.0, 400.0, 3.0,
                "New", "Priya Das", "Inquired on website yesterday for 3kW rooftop system."
            )
        ]

        for lead in initial_leads:
            cursor.execute("""
            INSERT INTO leads (
                name, phone, email, address, city, state, pincode,
                consumer_no, discom, category, sanctioned_load, avg_monthly_bill,
                roof_area_sqft, proposed_capacity_kw, status, assigned_to, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, lead)

        # 3. Default Site Surveys for leads 1, 2, 3, 6
        surveys = [
            (1, "2026-10-15", "Soumya Ranjan", "RCC Flat", 650.0, 580.0, 180.0, 20.0, 5.0, "3-Phase", "Single Phase Digital", 20.0, 12.0, 1, "Feasible", "Shadow-free RCC roof with good southern exposure."),
            (2, "2026-10-18", "Soumya Ranjan", "RCC Flat", 450.0, 420.0, 180.0, 20.0, 3.0, "1-Phase", "Digital Smart Meter", 15.0, 10.0, 1, "Feasible", "Ideal 3kW installation for PM Surya Ghar subsidy."),
            (3, "2026-10-05", "Soumya Ranjan", "Elevated Pergola", 950.0, 850.0, 175.0, 22.0, 8.0, "3-Phase", "3-Phase Digital", 35.0, 20.0, 1, "Feasible with modifications", "Elevated 7ft HDG structure recommended to allow roof usage."),
            (6, "2026-09-20", "Bikash Mohapatra", "RCC Flat", 750.0, 700.0, 180.0, 20.0, 6.0, "3-Phase", "3-Phase Digital", 22.0, 14.0, 1, "Feasible", "Clear terrace, dedicated earthing pits provisioned.")
        ]
        for s in surveys:
            cursor.execute("""
            INSERT INTO site_surveys (
                lead_id, survey_date, surveyor_name, roof_type, available_roof_area,
                shadow_free_area, azimuth_deg, tilt_angle, recommended_capacity_kw,
                existing_connection_phase, meter_status, cable_distance_dc_m, cable_distance_ac_m,
                earth_pit_space, feasibility_status, remarks
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, s)

        # 4. Default Quotations (5% GST, net meter 3500, transport 2500, subsidy ₹1,38,000 for Odisha)
        quotes = [
            ("QT-2026-0101", 1, 5.0, "Waaree 550Wp Mono PERC Bifacial", 10, "Growatt 5kW 3-Phase On-Grid", "HDG Heavy Duty (Wind 150 km/h)", "Polycab 4sqmm DC Cable, Havells AC Cable, SPD, Dual Earthing", 235000.0, 5.0, 11750.0, 3500.0, 2500.0, 252750.0, 138000.0, 114750.0, 21.0, 625.0, 3750.0, 2.5, 15, "Sent"),
            ("QT-2026-0098", 2, 3.0, "Adani 540Wp Mono PERC Half-cut", 6, "Solis 3kW Single-Phase On-Grid", "HDG Standard Flat Roof", "Solar Grade DC Cable 4sqmm, Copper Earthing Electrodes", 148000.0, 5.0, 7400.0, 3500.0, 2000.0, 160900.0, 138000.0, 22900.0, 12.6, 375.0, 2250.0, 0.9, 15, "Accepted"),
            ("QT-2026-0085", 3, 8.0, "Vikram Solar 550Wp Mono PERC", 16, "Sungrow 8kW 3-Phase On-Grid", "Super Structure Elevated (7ft Clear)", "Polycab DC, Finolex AC, 3 Earth Pits, Class-II SPD", 390000.0, 5.0, 19500.0, 4500.0, 3500.0, 417500.0, 138000.0, 279500.0, 33.6, 1000.0, 6000.0, 3.9, 15, "Accepted"),
            ("QT-2026-0072", 6, 6.0, "Tata Power Solar 545Wp Bifacial", 12, "Fronius 6kW 3-Phase On-Grid", "HDG Standard Rooftop", "Complete BOS Kit, 3 Earthing Pits, Copper Lightning Arrester", 295000.0, 5.0, 14750.0, 3500.0, 2500.0, 315750.0, 138000.0, 177750.0, 25.2, 750.0, 4500.0, 3.3, 15, "Accepted")
        ]
        for q in quotes:
            cursor.execute("""
            INSERT INTO quotations (
                quote_no, lead_id, capacity_kw, panel_make, panel_qty, inverter_make,
                structure_type, bos_details, system_cost, gst_rate, gst_amount,
                net_meter_cost, transportation_cost, total_project_cost, subsidy_eligible,
                net_customer_cost, daily_generation_kwh, monthly_generation_kwh,
                monthly_savings, payback_period_years, validity_days, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, q)

        # 5. Projects
        projects = [
            ("PRJ-2026-0012", 2, 2, 3.0, 160900.0, "DISCOM Application", 35, "Amit Mohanty", "2026-10-22", "2026-11-30", None, "01B9876543", "TPCODL", "Token advance ₹25,000 received. DISCOM paperwork submitted."),
            ("PRJ-2026-0009", 3, 3, 8.0, 417500.0, "Structure & Mounting", 65, "Amit Mohanty", "2026-10-10", "2026-11-25", None, "02C4567891", "TPCODL", "Module mounting completed. Inverter cabling scheduled tomorrow."),
            ("PRJ-2026-0004", 6, 4, 6.0, 315750.0, "Commissioned", 100, "Bikash Mohapatra", "2026-09-25", "2026-10-28", "2026-10-27", "05F5566778", "TPSODL", "Bi-directional Net meter installed and generating clean solar power.")
        ]
        for p in projects:
            cursor.execute("""
            INSERT INTO projects (
                project_code, lead_id, quote_id, capacity_kw, contract_value, stage,
                progress_pct, project_manager, start_date, target_commissioning_date,
                actual_commissioning_date, consumer_no, discom, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, p)

        # 6. DISCOM Applications
        discom_apps = [
            (1, 2, "TPCODL", "Bhubaneswar Division-II", "Chandrasekharpur Sub-Div", "01B9876543", "TPCODL/RTS/2026/8941", 3.0, 3.0, "2026-10-24", "Feasibility Approved", "2026-10-28", 2500.0, 1, None, None, None, "PM-SG-2026-78432", "Approved by DISCOM", 138000.0),
            (2, 3, "TPCODL", "Cuttack Central", "Station Road Sub-Div", "02C4567891", "TPCODL/RTS/2026/8120", 8.0, 8.0, "2026-10-12", "Meter Test Done", "2026-10-16", 4500.0, 1, "MTR-2026-5541", None, None, "PM-SG-2026-66319", "Pending Inspection", 138000.0),
            (3, 6, "TPSODL", "Berhampur Division", "Brahma Nagar Sub-Div", "05F5566778", "TPSODL/RTS/2026/7211", 6.0, 6.0, "2026-09-28", "Commissioned", "2026-10-02", 3500.0, 1, "MTR-2026-3890", "2026-10-26", "2026-10-27", "PM-SG-2026-51200", "Disbursed", 138000.0)
        ]
        for da in discom_apps:
            cursor.execute("""
            INSERT INTO discom_applications (
                project_id, lead_id, discom_name, division, sub_division,
                consumer_no, application_ref_no, applied_capacity_kw, sanctioned_load_kw,
                application_date, feasibility_status, feasibility_approval_date,
                demand_note_amount, demand_note_paid, bi_directional_meter_no,
                meter_installed_date, sync_date, subsidy_portal_ack,
                subsidy_status, subsidy_amount
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, da)

        # 7. Invoices (Both Proforma Invoices & Tax Invoices with 5% GST)
        invoices = [
            ("PI-2026-0012", 1, 2, "Proforma Invoice", "Advance Booking (15%)", 22200.0, 5.0, 1110.0, 3500.0, 2000.0, 28810.0, "2026-10-20", "2026-10-25", "Paid", 28810.0, "Initial advance booking proforma invoice."),
            ("INV-2026-0041", 1, 2, "Tax Invoice", "Material Dispatch (60%)", 88800.0, 5.0, 4440.0, 0.0, 0.0, 93240.0, "2026-10-28", "2026-11-05", "Paid", 93240.0, "Formal GST Tax Invoice for solar panels and structure dispatch."),
            ("PI-2026-0018", 2, 3, "Proforma Invoice", "Installation Advance", 60000.0, 5.0, 3000.0, 0.0, 0.0, 63000.0, "2026-10-15", "2026-10-22", "Paid", 63000.0, "Proforma billing before site mobilization."),
            ("INV-2026-0038", 2, 3, "Tax Invoice", "Material Dispatch (60%)", 234000.0, 5.0, 11700.0, 4500.0, 3500.0, 253700.0, "2026-10-18", "2026-10-25", "Paid", 253700.0, "GST Tax Invoice for 8kW equipment delivery."),
            ("INV-2026-0039", 2, 3, "Tax Invoice", "Installation Milestone (20%)", 78000.0, 5.0, 3900.0, 0.0, 0.0, 81900.0, "2026-11-05", "2026-11-15", "Partially Paid", 50000.0, "Balance ₹31,900 pending post inspection."),
            ("INV-2026-0025", 3, 6, "Tax Invoice", "Full Project Settlement", 295000.0, 5.0, 14750.0, 3500.0, 2500.0, 315750.0, "2026-10-27", "2026-11-05", "Paid", 315750.0, "Final tax invoice upon commissioning.")
        ]
        for inv in invoices:
            cursor.execute("""
            INSERT INTO invoices (
                invoice_no, project_id, lead_id, invoice_type, milestone_name,
                base_amount, gst_rate, gst_amount, net_meter_cost, transportation_cost,
                total_amount, invoice_date, due_date, status, paid_amount, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, inv)

        # 8. Payments Ledger (Payment In, Payment Out, and Project Expenses)
        payments = [
            # Payment In (Customer Receipts)
            ("RCT-2026-0041", "Payment In", "Debashish Pattnaik", "Customer Collection", 1, 1, 2, 28810.0, "2026-10-20", "UPI", "UPI/629584729102", "Verified", "Booking token via PhonePe"),
            ("RCT-2026-0035", "Payment In", "Manoj Kumar Sahoo", "Customer Collection", 2, 3, 3, 63000.0, "2026-10-15", "NEFT/RTGS", "HDFCR5202610128912", "Verified", "Advance booking NEFT"),
            ("RCT-2026-0038", "Payment In", "Manoj Kumar Sahoo", "Customer Collection", 2, 4, 3, 253700.0, "2026-10-19", "NEFT/RTGS", "HDFCR5202610197723", "Verified", "Material delivery payment"),
            ("RCT-2026-0044", "Payment In", "Manoj Kumar Sahoo", "Customer Collection", 2, 5, 3, 50000.0, "2026-11-06", "UPI", "UPI/631100994411", "Verified", "Installation partial milestone"),
            ("RCT-2026-0025", "Payment In", "Dr. Niranjan Behera", "Customer Collection", 3, 6, 6, 315750.0, "2026-10-27", "NEFT/RTGS", "SBIN002610279944", "Verified", "Final settlement on net meter sync"),
            
            # Payment Out (Vendor / Supplier Payments)
            ("VPO-2026-0012", "Payment Out", "Waaree Energies Ltd", "Modules & Inverters", 2, None, None, 185000.0, "2026-10-16", "NEFT/RTGS", "NEFT/WAAR/889921", "Verified", "Procurement of 16x 550Wp Mono PERC Modules"),
            ("VPO-2026-0015", "Payment Out", "Sungrow Power India", "Modules & Inverters", 2, None, None, 48000.0, "2026-10-17", "NEFT/RTGS", "NEFT/SUNG/441209", "Verified", "8kW 3-Phase On-Grid Inverter purchase"),
            ("VPO-2026-0018", "Payment Out", "Tata Power Solar Systems", "Modules & Inverters", 3, None, None, 142000.0, "2026-09-26", "NEFT/RTGS", "NEFT/TATA/992144", "Verified", "Solar Panels batch delivery for Berhampur site"),

            # Project Expenses (Site Execution & Miscellaneous)
            ("EXP-2026-0021", "Project Expense", "Raju Fabrication & Mounting Team", "Site Labor & Civil", 2, None, None, 16500.0, "2026-10-21", "Cash", "VOUCHER-089", "Verified", "Elevated super-structure fabrication labor charges"),
            ("EXP-2026-0024", "Project Expense", "Odisha Cargo & Logistics", "Transportation", 2, None, None, 4500.0, "2026-10-18", "UPI", "UPI/CARGO/11029", "Verified", "Delivery from godown to Cuttack terrace site"),
            ("EXP-2026-0028", "Project Expense", "TPCODL Liaisoning & Meter Testing", "DISCOM Liaisoning", 2, None, None, 4500.0, "2026-10-14", "UPI", "UPI/TPCODL/5521", "Verified", "Official demand note & meter testing fees"),
            ("EXP-2026-0031", "Project Expense", "Bikash Electricals", "Electrical & BoS", 3, None, None, 8200.0, "2026-10-04", "Cash", "VOUCHER-104", "Verified", "Dual chemical earthing compound and copper lightning arrester")
        ]
        for pay in payments:
            cursor.execute("""
            INSERT INTO payments (
                receipt_no, transaction_type, party_name, category, project_id,
                invoice_id, lead_id, amount, payment_date, payment_mode,
                reference_no, status, remarks
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, pay)

    conn.commit()

if __name__ == "__main__":
    init_db()
    print("Database initialized and seeded successfully.")
