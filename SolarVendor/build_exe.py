"""
PyInstaller build script for SolarPulse ERP.
Creates a standalone, optimized distribution folder with app_icon.ico.
"""

import os
import sys
import subprocess
import shutil

def build():
    print("=" * 60)
    print("  Building SolarPulse ERP Executable with PyInstaller...")
    print("=" * 60)

    # Clean old build/dist
    shutil.rmtree("build", ignore_errors=True)
    shutil.rmtree("dist", ignore_errors=True)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=SolarPulse_ERP",
        "--onedir",
        "--windowed", # Windows GUI application (no ugly black CMD box)
        "--icon=app_icon.ico",
        "--add-data=app/static;app/static",
        "--add-data=app_icon.ico;.",
        "--add-data=version.json;.",
        "--collect-all=uvicorn",
        "--hidden-import=uvicorn.logging",
        "--hidden-import=uvicorn.loops",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.protocols",
        "--hidden-import=uvicorn.protocols.http",
        "--hidden-import=uvicorn.protocols.http.auto",
        "--hidden-import=uvicorn.protocols.http.h11_impl",
        "--hidden-import=uvicorn.protocols.http.httptools_impl",
        "--hidden-import=uvicorn.protocols.websockets",
        "--hidden-import=uvicorn.protocols.websockets.auto",
        "--hidden-import=uvicorn.lifespan",
        "--hidden-import=uvicorn.lifespan.off",
        "--hidden-import=uvicorn.lifespan.on",
        "--hidden-import=logging.config",
        "--hidden-import=reportlab",
        "--hidden-import=reportlab.platypus",
        "--hidden-import=reportlab.lib",
        "--hidden-import=openpyxl",
        "--hidden-import=pandas",
        "--hidden-import=sqlite3",
        "--noconfirm",
        "run.py"
    ]

    print("Running command:", " ".join(cmd))
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print("PyInstaller build failed!")
        sys.exit(1)

    print("\nPyInstaller build completed successfully!")
    print("Output folder: dist/SolarPulse_ERP")

if __name__ == "__main__":
    build()
