import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont('Helvetica', 9)
        self.setFillColor(colors.HexColor('#6b7280'))
        self.drawString(54, 36, 'Beyond Excel Solution — Master Projects & AI Handover Guide')
        self.drawRightString(612 - 54, 36, f'Page {self._pageNumber} of {page_count}')
        self.setStrokeColor(colors.HexColor('#e5e7eb'))
        self.setLineWidth(0.5)
        self.line(54, 48, 612 - 54, 48)
        self.restoreState()

def create_guide_pdf(pdf_path):
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1e3a8a')
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#4b5563')
    )
    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1e40af'),
        spaceBefore=12,
        spaceAfter=5
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=4
    )
    code_style = ParagraphStyle(
        'CodeBlock',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#111827'),
        backColor=colors.HexColor('#f3f4f6'),
        borderPadding=5,
        spaceBefore=3,
        spaceAfter=5
    )

    story = []

    # Title & Header
    story.append(Paragraph('Beyond Excel Solution — Master Projects Repository', title_style))
    story.append(Paragraph('Client Software Architectures & AI Handover Specification', ParagraphStyle('SubHeader', parent=title_style, fontSize=12, leading=15, textColor=colors.HexColor('#2563eb'))))
    story.append(Spacer(1, 4))
    story.append(Paragraph('<b>GitHub Organization / Owner:</b> <code>beyondexcelsolution-web</code>', subtitle_style))
    story.append(Paragraph('<b>Master GitHub Repo:</b> <code>https://github.com/beyondexcelsolution-web/Projects.git</code>', subtitle_style))
    story.append(Paragraph('<b>Local Master Git Root:</b> <code>C:\\Users\\pramo\\PycharmProjects\\Projects</code>', subtitle_style))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width='100%', thickness=1.5, color=colors.HexColor('#2563eb'), spaceBefore=2, spaceAfter=8))

    # Section 1
    story.append(Paragraph('1. Monorepo Architecture & Directory Structure', h1_style))
    story.append(Paragraph('All agency client projects are managed within one single master repository, so developers and AIs never repeat repo creation:', body_style))

    dir_text = (
        'C:\\Users\\pramo\\PycharmProjects\\Projects\\       &lt;-- Master GitHub Repository Root<br/>'
        '├── .gitignore                                 &lt;-- Global exclusions for all projects<br/>'
        '├── push_all_to_github.bat                     &lt;-- 1-Click push script for all projects<br/>'
        '├── github_sync_all.py                         &lt;-- Python sync automation script<br/>'
        '├── README.md                                  &lt;-- Master projects overview<br/>'
        '│<br/>'
        '├── Seatmanagementschool\\                      &lt;-- Client 1: Crescent Islamic High School<br/>'
        '│   ├── app.py                                 &lt;-- Flask Controller & Routes<br/>'
        '│   ├── database.py                            &lt;-- SQLite Database Manager<br/>'
        '│   ├── seating_engine.py                      &lt;-- Seating Algorithm Engine<br/>'
        '│   ├── excel_importer.py                      &lt;-- Dynamic Importer (Dynamic_Report.xlsx)<br/>'
        '│   ├── docx_exporter.py                       &lt;-- Official Word Documents Generator<br/>'
        '│   ├── consolidated_engine.py                 &lt;-- Consolidated Marks Sheet Generator<br/>'
        '│   ├── build_exe.spec                         &lt;-- PyInstaller Build Script<br/>'
        '│   └── installer.iss                          &lt;-- Inno Setup 6 Installer Script<br/>'
        '│<br/>'
        '└── [Future_Client_Projects]\\                  &lt;-- Client 2, Client 3, etc.'
    )
    story.append(Paragraph(dir_text, code_style))

    # Section 2: Component Matrix
    story.append(Paragraph('2. Crescent Seat Management — Component Matrix', h1_style))
    table_data = [
        [Paragraph('<b>Module</b>', body_style), Paragraph('<b>Stack</b>', body_style), Paragraph('<b>Functionality</b>', body_style)],
        [Paragraph('<code>app.py</code>', body_style), Paragraph('Flask / Jinja2', body_style), Paragraph('Dashboard, CRUD for Students, Rooms, Arrangements, Preview and Export routes.', body_style)],
        [Paragraph('<code>excel_importer.py</code>', body_style), Paragraph('openpyxl', body_style), Paragraph('Dynamic header detection. Auto-maps 6 HIFZ, 11G/11B, 12G/12B, Hindi exemptions.', body_style)],
        [Paragraph('<code>seating_engine.py</code>', body_style), Paragraph('Python / SQLite', body_style), Paragraph('Validates 100% capacity, assigns Left/Right bench pairs, prevents duplicates.', body_style)],
        [Paragraph('<code>docx_exporter.py</code>', body_style), Paragraph('python-docx', body_style), Paragraph('Generates official A4 exam notice boards, class plans, attendance sheets with banner.', body_style)],
        [Paragraph('<code>consolidated_engine.py</code>', body_style), Paragraph('openpyxl / docx', body_style), Paragraph('Builds class-wise marks entry templates for teachers directly from imported database.', body_style)],
        [Paragraph('<code>main.py</code>', body_style), Paragraph('Waitress WSGI', body_style), Paragraph('Starts background multithreaded server and launches native desktop window.', body_style)]
    ]
    t = Table(table_data, colWidths=[110, 85, 309])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f0f9ff')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#0369a1')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t)
    story.append(Spacer(1, 6))

    # Section 3: GitHub Commands
    story.append(Paragraph('3. GitHub Commands for Developers & AI', h1_style))
    gh_steps = (
        '# Step 1: Open Terminal in Master Projects folder<br/>'
        'cd "C:\\Users\\pramo\\PycharmProjects\\Projects"<br/><br/>'
        '# Step 2: Initialize & set remote<br/>'
        'git init<br/>'
        'git branch -M main<br/>'
        'git remote add origin https://github.com/beyondexcelsolution-web/Projects.git<br/><br/>'
        '# Step 3: Commit and push all client projects<br/>'
        'git add .<br/>'
        'git commit -m "Add Seatmanagementschool client project"<br/>'
        'git push -u origin main'
    )
    story.append(Paragraph(gh_steps, code_style))

    # Section 4: AI Instructions
    story.append(Paragraph('4. Operational Instructions for Future AI Agents (Cursor / Claude)', h1_style))
    ai_rules = (
        '1. <b>Editing:</b> Edit code in <code>C:\\Users\\pramo\\PycharmProjects\\Projects\\[ProjectName]</code>.<br/>'
        '2. <b>Verification:</b> In Seatmanagementschool, run <code>python test_suite.py</code> (must be 8/8 OK).<br/>'
        '3. <b>Build Executable:</b> Run <code>pyinstaller build_exe.spec --noconfirm</code> in the project folder.<br/>'
        '4. <b>Build Installer:</b> Run <code>& "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe" installer.iss</code>.<br/>'
        '5. <b>Push to GitHub:</b> Run <code>push_all_to_github.bat</code> or git commit & push in the Projects root.'
    )
    story.append(Paragraph(ai_rules, body_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f'PDF generated successfully at: {pdf_path} ({os.path.getsize(pdf_path)} bytes)')

if __name__ == '__main__':
    p1 = r'C:\Users\pramo\PycharmProjects\Projects\AI_MASTER_PROJECTS_GUIDE.pdf'
    p2 = r'C:\Users\pramo\PycharmProjects\Projects\Seatmanagementschool\AI_MASTER_PROJECTS_GUIDE.pdf'
    p3 = r'c:\Users\pramo\PycharmProjects\Seatmanagementschool\AI_MASTER_PROJECTS_GUIDE.pdf'
    create_guide_pdf(p1)
    create_guide_pdf(p2)
    create_guide_pdf(p3)
