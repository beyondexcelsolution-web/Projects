# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

added_files = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('instance', 'instance'),
    ('consoliataed sheet PA 2.xlsx', '.'),
    ('consolidated_subject_mapping.json', '.'),
    ('version.json', '.'),
]

hidden_imports = [
    'license_manager',
    'updater',
    'version',
    'requests',
    'waitress',
    'waitress.adjustments',
    'waitress.channel',
    'waitress.server',
    'openpyxl',
    'openpyxl.cell',
    'openpyxl.styles',
    'docx',
    'docx.oxml',
    'docx.oxml.ns',
    'jinja2',
    'jinja2.ext',
    'werkzeug',
    'werkzeug.serving',
    'sqlite3',
    'json',
    'urllib',
    'urllib.request',
    'hashlib',
    'platform',
    'database',
    'paths',
    'seating_engine',
    'docx_exporter',
    'excel_exporter',
    'excel_importer',
    'consolidated_engine',
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CrescentIslamicHighSchool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon.ico'
)
