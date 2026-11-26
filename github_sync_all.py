#!/usr/bin/env python3
"""
Master GitHub Sync Tool for All Client Projects
Repository: beyondexcelsolution-web/Projects
"""

import os
import sys
import subprocess
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GITHUB_OWNER = "beyondexcelsolution-web"
GITHUB_REPO = "Projects"
REMOTE_URL = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}.git"

def run_git_cmd(args):
    try:
        res = subprocess.run(['git'] + args, cwd=SCRIPT_DIR, capture_output=True, text=True)
        return res.returncode == 0, res.stdout.strip(), res.stderr.strip()
    except FileNotFoundError:
        return False, "", "git command not found"

def check_git_installed():
    ok, out, _ = run_git_cmd(['--version'])
    return ok, out

def sync_projects(commit_msg):
    git_ok, git_ver = check_git_installed()
    if not git_ok:
        print("[!] Git CLI is not installed yet.")
        print("    Download & install Git from: https://git-scm.com/download/win")
        return

    print(f"[✓] Git detected: {git_ver}")

    # Check if repo is initialized
    if not os.path.exists(os.path.join(SCRIPT_DIR, '.git')):
        print("[*] Initializing local master Git repository...")
        run_git_cmd(['init'])
        run_git_cmd(['branch', '-M', 'main'])

    # Ensure remote origin is set
    _, remotes, _ = run_git_cmd(['remote', '-v'])
    if 'origin' not in remotes:
        print(f"[*] Setting remote origin to: {REMOTE_URL}")
        run_git_cmd(['remote', 'add', 'origin', REMOTE_URL])
    else:
        run_git_cmd(['remote', 'set-url', 'origin', REMOTE_URL])

    print("[*] Staging all projects...")
    run_git_cmd(['add', '.'])

    print(f"[*] Committing: {commit_msg}")
    ok, out, err = run_git_cmd(['commit', '-m', commit_msg])
    if not ok and 'nothing to commit' in (out + err):
        print("[i] Everything is up-to-date (nothing to commit).")
    elif not ok:
        print(f"[!] Commit info: {err or out}")

    print(f"[*] Pushing to {REMOTE_URL} (branch: main)...")
    ok, out, err = run_git_cmd(['push', '-u', 'origin', 'main'])
    if ok:
        print(f"\n[✓] Push successful! All projects updated on GitHub:")
        print(f"    https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}")
    else:
        print(f"[!] Push notice: {err or out}")
        print("    If authentication is prompted, sign in via browser or Personal Access Token.")

if __name__ == '__main__':
    msg = sys.argv[2] if len(sys.argv) > 2 else "Update projects repository"
    sync_projects(msg)
