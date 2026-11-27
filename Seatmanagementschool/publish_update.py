"""
Crescent Islamic High School - Automated Update Publisher Script
================================================================
This script automates building the executable, compiling the Inno Setup installer,
updating version.json with release notes, syncing with the GitHub monorepo, and pushing
to GitHub. Once pushed, any user PC running the app will see the update immediately!
"""

import os
import sys
import json
import time
import shutil
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MONOREPO_DIR = r"C:\Users\pramo\PycharmProjects\Projects\Seatmanagementschool"
GIT_EXE = r"C:\Users\pramo\AppData\Local\Programs\MinGit\cmd\git.exe"
INNO_COMPILER = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

def run_cmd(cmd, cwd=None):
    print(f"\n>> Running: {cmd}")
    res = subprocess.run(cmd, shell=True, cwd=cwd or BASE_DIR)
    if res.returncode != 0:
        print(f"Error: Command failed with code {res.returncode}")
        return False
    return True

def main():
    print("=" * 72)
    print("   CRESCENT ISLAMIC HIGH SCHOOL - UPDATE PUBLISHER")
    print("=" * 72)

    # 1. Read current version
    version_file = os.path.join(BASE_DIR, 'version.json')
    if os.path.exists(version_file):
        with open(version_file, 'r', encoding='utf-8') as f:
            v_data = json.load(f)
            curr_ver = v_data.get('version', '2.1.0')
    else:
        curr_ver = '2.1.0'

    print(f"\nCurrent version in version.json: {curr_ver}")
    new_ver = input(f"Enter new version number [press Enter for {curr_ver}]: ").strip() or curr_ver

    # 2. Rebuild PyInstaller binary
    print("\n[1/5] Building application executable with PyInstaller...")
    if not run_cmd("pyinstaller build_exe.spec --noconfirm"):
        print("PyInstaller build failed. Aborting.")
        return

    # 3. Update installer.iss with new version
    iss_file = os.path.join(BASE_DIR, 'installer.iss')
    if os.path.exists(iss_file):
        with open(iss_file, 'r', encoding='utf-8') as f:
            iss_content = f.read()
        import re
        iss_content = re.sub(r'#define MyAppVersion "[^"]+"', f'#define MyAppVersion "{new_ver}"', iss_content)
        with open(iss_file, 'w', encoding='utf-8') as f:
            f.write(iss_content)
        print(f"Updated installer.iss with version {new_ver}")

    # 4. Compile Inno Setup installer
    print("\n[2/5] Compiling Inno Setup installer...")
    if not run_cmd(f'"{INNO_COMPILER}" "{iss_file}"'):
        print("Inno Setup compilation failed. Aborting.")
        return

    setup_exe = os.path.join(BASE_DIR, 'installer_output', 'Crescent_Islamic_High_School_Setup.exe')
    if os.path.exists(setup_exe):
        size_bytes = os.path.getsize(setup_exe)
        size_mb = f"{size_bytes / (1024 * 1024):.1f} MB"
        print(f"Installer built successfully: {size_mb}")
        
        # Also update zip
        zip_path = os.path.join(BASE_DIR, 'installer_output', 'Crescent_Islamic_High_School_Setup.zip')
        run_cmd(f'powershell -Command "Compress-Archive -Path \'{setup_exe}\' -DestinationPath \'{zip_path}\' -Force"')

    # 5. Update version.json
    print("\n[3/5] Updating version.json...")
    if os.path.exists(version_file):
        with open(version_file, 'r', encoding='utf-8') as f:
            v_data = json.load(f)
        v_data['version'] = new_ver
        v_data['release_date'] = time.strftime("%d-%b-%Y")
        v_data['filesize_bytes'] = size_bytes
        v_data['filesize_mb'] = size_mb
        with open(version_file, 'w', encoding='utf-8') as f:
            json.dump(v_data, f, indent=2)

    # 6. Sync files to Monorepo
    print("\n[4/5] Syncing files to Git Monorepo...")
    if os.path.exists(MONOREPO_DIR):
        # Sync code files
        for fname in ['app.py', 'seating_engine.py', 'docx_exporter.py', 'updater.py', 'version.py', 'version.json', 'installer.iss', 'build_exe.spec']:
            src = os.path.join(BASE_DIR, fname)
            dst = os.path.join(MONOREPO_DIR, fname)
            if os.path.exists(src):
                shutil.copy2(src, dst)
        
        # Sync templates
        shutil.copytree(os.path.join(BASE_DIR, 'templates'), os.path.join(MONOREPO_DIR, 'templates'), dirs_exist_ok=True)
        
        # Sync installer_output
        mono_installer_dir = os.path.join(MONOREPO_DIR, 'installer_output')
        os.makedirs(mono_installer_dir, exist_ok=True)
        shutil.copy2(setup_exe, os.path.join(mono_installer_dir, 'Crescent_Islamic_High_School_Setup.exe'))

    # 7. Git commit and push
    print("\n[5/5] Committing and pushing release to GitHub...")
    git_dir = os.path.dirname(MONOREPO_DIR)
    run_cmd(f'"{GIT_EXE}" -C "{git_dir}" add .')
    run_cmd(f'"{GIT_EXE}" -C "{git_dir}" commit -m "Release v{new_ver}: In-App Update and Seating Print Enhancements"')
    run_cmd(f'"{GIT_EXE}" -C "{git_dir}" push origin main')

    print("\n" + "=" * 72)
    print(f" SUCCESS: Version v{new_ver} published and pushed to GitHub!")
    print(" Any client PC will now see this update and can 1-click install it!")
    print("=" * 72)

if __name__ == '__main__':
    main()
