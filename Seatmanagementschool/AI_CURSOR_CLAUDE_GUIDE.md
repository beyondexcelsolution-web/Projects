# AI Cursor & Claude Integration Guide
## Crescent Islamic High School — Examination Seating Management System

> **Document Version:** 1.0  
> **Target Audience:** Future AI Agents (Cursor, Claude, Antigravity, ChatGPT) & Developers  
> **Last Updated:** November 2026  
> **Project Root (Git):** `C:\Users\pramo\PycharmProjects\Gitfolder\Seatmanagementschool`  
> **Primary Working Copy:** `C:\Users\pramo\PycharmProjects\Seatmanagementschool`  

---

## 1. Executive Summary & Purpose
This document provides complete architectural, operational, and Git synchronisation instructions for the **Crescent Islamic High School Examination Seating Management System**. 

Any AI assistant (Cursor, Claude, etc.) reading this file can immediately understand:
1. Where the project resides and how the folders are organised.
2. The complete technology stack and dependencies.
3. How to connect, commit, and push updates to the GitHub repository.
4. How to compile the standalone `.exe` and Inno Setup Windows installer.
5. Key database schemas, seating rules, and export engines.

---

## 2. Directory & Storage Architecture

The user maintains a dedicated, structured directory structure to prevent file collisions:

```
C:\Users\pramo\PycharmProjects\
│
├── Seatmanagementschool\                 <-- Active Working Directory (Dev / Tests / Builds)
│   ├── dist\                             <-- Compiled CrescentIslamicHighSchool.exe
│   ├── installer_output\                 <-- Compiled Crescent_Islamic_High_School_Setup.exe
│   └── instance\                         <-- Local SQLite Database (school_seats.db)
│
└── Gitfolder\                            <-- Dedicated Git Parent Directory
    └── Seatmanagementschool\             <-- Clean Git Repository Directory
        ├── .gitignore                    <-- Standard ignore rules
        ├── requirements.txt              <-- Python package dependencies
        ├── github_sync.py                <-- Automated GitHub synchronization script
        ├── push_to_github.bat            <-- 1-Click Windows batch script to push
        ├── AI_CURSOR_CLAUDE_GUIDE.md     <-- This documentation
        ├── AI_CURSOR_CLAUDE_GUIDE.pdf    <-- Compiled PDF version of this document
        ├── app.py                        <-- Flask Application & Web Controller
        ├── database.py                   <-- SQLite Schema & Connection Pool
        ├── seating_engine.py             <-- Seating Allocation & Health Checks
        ├── excel_importer.py             <-- Dynamic Excel/CSV Student Importer
        ├── docx_exporter.py              <-- Word (.docx) Official Printout Engine
        ├── excel_exporter.py             <-- Excel (.xlsx) Export Engine
        ├── consolidated_engine.py        <-- Consolidated Marks Sheet Engine
        ├── license_manager.py            <-- Offline License Key Verification
        ├── paths.py                      <-- AppData & Local Directory Resolver
        ├── main.py                       <-- Desktop Launcher (Waitress + Webview)
        ├── test_suite.py                 <-- 8-Test Automated Verification Suite
        ├── build_exe.spec                <-- PyInstaller 1-file .exe Specification
        ├── installer.iss                 <-- Inno Setup 6 64-bit Installer Script
        ├── templates\                    <-- Jinja2 HTML Templates (Clean School UI)
        └── static\                       <-- CSS, JS, Logos & Wide School Banner
```

---

## 3. Technology Stack & Key Dependencies

- **Language:** Python 3.10+ (64-bit Windows)
- **Web Framework:** Flask + Jinja2 (HTML5 / Bootstrap 5 / Modern CSS)
- **Production WSGI Server:** Waitress (multithreaded local server on `http://127.0.0.1:5000`)
- **Database:** SQLite 3 (`instance/school_seats.db` or `%LOCALAPPDATA%\CrescentSeatManagement\school_seats.db`)
- **Excel Processing:** `openpyxl` (dynamic header scanning, formulas, styles)
- **Word Document Generation:** `python-docx` + custom XML elements (tables, headers, orientation)
- **Packaging & Distribution:**
  - Standalone Binary: PyInstaller (`build_exe.spec`)
  - Windows Installer: Inno Setup 6 (`installer.iss`)

---

## 4. Key Components & File Responsibilities

| File | Purpose |
| :--- | :--- |
| `app.py` | Flask routes (`/`, `/settings`, `/students`, `/rooms`, `/arrangement`, `/preview/*`, `/export/*`). Clean UI without update bloat. |
| `database.py` | Schema definitions (`settings`, `students`, `rooms`, `arrangements`). Thread-safe `get_db()`. |
| `excel_importer.py` | Dynamic column detection for client's dynamic reports (`Dynamic_Report.xlsx`) & template sheets. Automatically maps classes (`6 HIFZ`, `11 G`, `11 B`, `12 G`, `12 B`), blocks, and genders. |
| `seating_engine.py` | Reads arrangements table, cross-references students, pairs Left/Right benches, and validates 100% seating health. |
| `docx_exporter.py` | Generates pixel-perfect A4 Word documents with wide school banner, continuous attendance tables, and exact school headers. |
| `consolidated_engine.py` | Generates multi-tab Excel and Word consolidated marksheets with all subjects and marks columns from imported student records. |
| `main.py` | Starts Waitress WSGI server in background thread and launches native desktop browser window. |
| `test_suite.py` | Complete test suite (Dashboard, Settings, Students CRUD, Rooms CRUD, Arrangement CRUD, Previews, Downloads, Dynamic Import). |

---

## 5. GitHub Repository Setup & Connection Instructions

### Step 5.1: Repository Configuration
In `C:\Users\pramo\PycharmProjects\Gitfolder\Seatmanagementschool\github_config.json`:
```json
{
    "github_owner": "<YOUR_GITHUB_USERNAME>",
    "github_repo": "Seatmanagementschool",
    "github_token": "<OPTIONAL_PERSONAL_ACCESS_TOKEN>",
    "branch": "main",
    "app_version": "2.1.0"
}
```

### Step 5.2: Linking to GitHub Remote
To link this clean folder to your GitHub repository, run in terminal:
```bash
cd "C:\Users\pramo\PycharmProjects\Gitfolder\Seatmanagementschool"
git init
git branch -M main
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/Seatmanagementschool.git
```

### Step 5.3: Pushing Changes
Whenever changes are made:
```bash
cd "C:\Users\pramo\PycharmProjects\Gitfolder\Seatmanagementschool"
git add .
git commit -m "Describe your changes here"
git push -u origin main
```
*Alternatively, the user can double-click `push_to_github.bat` or run `python github_sync.py push "Commit message"`.*

---

## 6. How AI Agents (Cursor / Claude) Should Work With This Project

When an AI agent (Cursor, Claude, Antigravity) is prompted to add features or fix bugs:

1. **Perform Code Edits:**
   Edit the source files in `c:\Users\pramo\PycharmProjects\Seatmanagementschool`.
2. **Run Verification Tests:**
   Always run `python test_suite.py` to ensure all 8 tests pass without regression.
3. **Synchronise to Gitfolder:**
   Copy the modified files to `C:\Users\pramo\PycharmProjects\Gitfolder\Seatmanagementschool`.
4. **Build Distribution Binaries (When Requested):**
   - PyInstaller: `pyinstaller build_exe.spec --noconfirm`
   - Inno Setup: `& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss`
5. **Commit & Push:**
   Execute `git add .`, `git commit -m "<message>"`, and `git push origin main` inside `C:\Users\pramo\PycharmProjects\Gitfolder\Seatmanagementschool`.

---

## 7. Troubleshooting & FAQ for AI Assistants

- **Q: Why does `excel_importer.py` use dynamic column detection?**  
  *A:* Because client school exports have varying column headers (e.g. `'Student Adm-No'` instead of `'Adm No'`, `'Class Name'` instead of `'Class'`). The dynamic parser detects headers by scanning content and keywords automatically.

- **Q: Where is the SQLite database located?**  
  *A:* In dev mode, it is at `Seatmanagementschool\instance\school_seats.db`. When compiled to an `.exe`, it automatically points to `%LOCALAPPDATA%\CrescentSeatManagement\school_seats.db` via `paths.py` so user data is never lost during updates.

- **Q: Are binary `.exe` and `.db` files tracked by Git?**  
  *A:* No. `.gitignore` strictly excludes `dist/`, `build/`, `installer_output/`, and `instance/*.db`. Binary releases are published as GitHub Releases, while Git tracks pure source code and documentation.

---
*Generated automatically for Crescent Islamic High School Seat Management System.*
