# Beyond Excel Solution — Master Projects & AI Handover Guide
## Central Monorepo for All Client Software Solutions

> **Owner / Organization:** `beyondexcelsolution-web`  
> **Master Repository:** `https://github.com/beyondexcelsolution-web/Projects.git`  
> **Master Local Directory:** `C:\Users\pramo\PycharmProjects\Projects`  
> **Target Audience:** Future AI Agents (Cursor, Claude, Antigravity) & Developers  
> **Last Updated:** November 2026  

---

## 1. Purpose & Monorepo Architecture
All client software projects of **Beyond Excel Solution** are organized in this single master repository. 
You **never** need to create separate repositories for each project. All current and future client projects live side-by-side as distinct subfolders.

### Master Folder Structure:
```
C:\Users\pramo\PycharmProjects\Projects\        <-- Master Git Root (Monorepo)
│
├── .gitignore                                  <-- Global Git ignore rules
├── README.md                                   <-- Master projects overview
├── push_all_to_github.bat                      <-- 1-Click push script for all projects
├── github_sync_all.py                          <-- Python sync automation tool
├── AI_MASTER_PROJECTS_GUIDE.pdf                <-- Master Handover PDF
├── AI_MASTER_PROJECTS_GUIDE.md                 <-- This Documentation
│
├── Seatmanagementschool\                       <-- Project 1: Crescent Islamic High School
│   ├── app.py                                  <-- Flask Controller
│   ├── database.py                             <-- SQLite Schema & Tables
│   ├── seating_engine.py                       <-- Seating Allocation Logic
│   ├── excel_importer.py                       <-- Dynamic Excel/CSV Importer
│   ├── docx_exporter.py                        <-- Word (.docx) Exporter
│   ├── consolidated_engine.py                  <-- Consolidated Marksheet Engine
│   ├── test_suite.py                           <-- 8-Test Verification Suite
│   ├── build_exe.spec                          <-- PyInstaller .exe Spec
│   ├── installer.iss                           <-- Inno Setup 6 Script
│   ├── templates\                              <-- HTML5 / Bootstrap 5 Templates
│   └── static\                                 <-- CSS, JS & School Banner
│
└── [Future_Client_Projects]\                   <-- Project 2, Project 3, etc.
```

---

## 2. Project 1: Crescent Seat Management System

- **Stack:** Python 3.10+, Flask, Waitress WSGI, SQLite, `openpyxl`, `python-docx`
- **Purpose:** Full examination seat allocation, room notice boards, attendance registers, and consolidated marksheets for Crescent Islamic High School.
- **Dynamic Import:** `excel_importer.py` automatically detects headers in `Dynamic_Report.xlsx`, normalizes `6 HIFZ`, splits 11 & 12 into `11 G` / `11 B` and `12 G` / `12 B`, assigns class & group roll numbers, and flags Hindi exemptions.
- **Verification:** Run `python test_suite.py` inside `Seatmanagementschool`. All 8 tests must pass 100%.

---

## 3. GitHub Remote Linking

To link this master folder to your GitHub repository:
```bash
cd "C:\Users\pramo\PycharmProjects\Projects"
git init
git branch -M main
git remote add origin https://github.com/beyondexcelsolution-web/Projects.git
git add .
git commit -m "Initialize master projects monorepo with Seatmanagementschool"
git push -u origin main
```

---

## 4. Instructions for Future AI Agents (Cursor / Claude)

1. **Adding a New Client Project:**
   Create a new folder inside `C:\Users\pramo\PycharmProjects\Projects\<NewClientName>\` and place project files there.
2. **Editing an Existing Project:**
   Modify the code inside its subfolder (e.g. `Projects\Seatmanagementschool\`).
3. **Running Tests:**
   Always run test suites inside the project subfolder before committing.
4. **Pushing to GitHub:**
   In the root directory `C:\Users\pramo\PycharmProjects\Projects`, run:
   ```bash
   git add .
   git commit -m "Update <ProjectName>: <description>"
   git push origin main
   ```
   Or double-click `push_all_to_github.bat`.

---
*Created for Beyond Excel Solution.*
