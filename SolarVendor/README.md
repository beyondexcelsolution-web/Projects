# SolarPulse ERP - Professional Solar EPC Management System
**Version:** 2.0.0 (Production Release)
**Developer:** Beyond Excel Solution
**Target OS:** Windows 10 / 11 (64-bit)

## Overview
Comprehensive ERP and CRM designed specifically for Solar EPC Vendors and Installers handling PM Surya Ghar Muft Bijli Yojana residential and commercial solar installations in Odisha (TPCODL, TPNODL, TPWODL) and pan-India.

## Core Modules & Features
- **Leads & CRM Pipeline:** Tracking inquiries, lead stages, sanitized contact information.
- **Site Feasibility & Shadow Analysis:** Roof structure, survey photo records, GPS coordinates.
- **Smart Solar System Sizing Calculator:** Live monthly electricity bill to kW sizing, Rs. 1,38,000 PM Surya Ghar subsidy, Odisha state solar subsidies, 5% solar GST, and payback ROI models.
- **Quotation Generator:** Instant generation of professional customer quotations.
- **Projects & Work Order Management:** Milestone progression (Structure, Panels, Inverter, Wiring, Testing, Grid Sync).
- **DISCOM & Net Metering Tracker:** End-to-end tracking of TPCODL / TPNODL / TPWODL meter approvals, feasibility reports, and bi-directional meter synchronization.
- **Invoicing & Billing:** Separate categories for Proforma Invoice & Official Tax Invoice.
- **3-Way Financial Ledger:** Payment In, Payment Out (Suppliers & Vendors), and Project Expenses.
- **Executive Analytics & Multi-Sheet Excel Reports:** Downloadable master .xlsx workbooks and client proposals.
- **1-Click In-App Express Auto-Update:** Built-in cloud sync with GitHub (`beyondexcelsolution-web/Projects`). Detects newer releases, downloads chunked packages in the background, and updates silently without redirecting users to external websites.

## Direct Installer Download
The standalone, pre-compiled Windows setup wizard is located at:
`dist_installer/SolarPulse_ERP_Setup_7Day_Demo.exe`

## Building from Source
1. Install dependencies:
   `pip install fastapi uvicorn reportlab openpyxl pandas pydantic`
2. Build standalone executable:
   `python build_exe.py`
3. Compile Inno Setup installer:
   `ISCC.exe installer.iss`
