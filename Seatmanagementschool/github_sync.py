#!/usr/bin/env python3
"""
GitHub Sync & Automation Tool
Crescent Islamic High School - Seat Management System

Usage:
  python github_sync.py push "Commit message"
  python github_sync.py release v2.2.0 "Release notes"
  python github_sync.py status
"""

import os
import sys
import json
import base64
import urllib.request
import urllib.error
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, 'github_config.json')

def load_config():
    default_config = {
        "github_owner": "",
        "github_repo": "Seatmanagementschool",
        "github_token": "",
        "branch": "main",
        "app_version": "2.1.0"
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                default_config.update(cfg)
        except Exception as e:
            print(f"[!] Warning reading config: {e}")
    return default_config

def save_config(cfg):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=4)
    print(f"[✓] Configuration saved to {CONFIG_FILE}")

def run_git_cmd(args):
    try:
        res = subprocess.run(['git'] + args, cwd=SCRIPT_DIR, capture_output=True, text=True)
        return res.returncode == 0, res.stdout.strip(), res.stderr.strip()
    except FileNotFoundError:
        return False, "", "git command not found"

def check_git_installed():
    ok, out, _ = run_git_cmd(['--version'])
    return ok, out

def check_remote_status(config):
    owner = config.get('github_owner')
    repo = config.get('github_repo')
    token = config.get('github_token')

    if not owner or not repo:
        print("[!] GitHub owner or repo name not configured in github_config.json.")
        return False

    url = f"https://api.github.com/repos/{owner}/{repo}"
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'SeatManagementSync/1.0')
    req.add_header('Accept', 'application/vnd.github.v3+json')
    if token:
        req.add_header('Authorization', f'token {token}')

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print(f"[✓] Repository exists: {data.get('html_url')}")
            print(f"    Visibility: {'Private' if data.get('private') else 'Public'}")
            print(f"    Default branch: {data.get('default_branch')}")
            return True
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"[i] Repository '{owner}/{repo}' does not exist on GitHub yet.")
        elif e.code == 401:
            print("[!] Authentication failed. Check your GitHub Token in github_config.json.")
        else:
            print(f"[!] HTTP Error {e.code}: {e.reason}")
        return False
    except Exception as e:
        print(f"[!] Connection error: {e}")
        return False

def git_push_flow(commit_msg):
    git_ok, git_ver = check_git_installed()
    if not git_ok:
        print("[!] Git CLI is not installed on this system.")
        print("    Please install Git for Windows (https://git-scm.com/download/win)")
        print("    OR configure your GitHub Personal Access Token in github_config.json to push via API.")
        return

    print(f"[✓] Detected: {git_ver}")
    # 1. Check if git repo initialized
    if not os.path.exists(os.path.join(SCRIPT_DIR, '.git')):
        print("[*] Initializing local Git repository...")
        run_git_cmd(['init'])
        run_git_cmd(['branch', '-M', 'main'])

    cfg = load_config()
    owner = cfg.get('github_owner')
    repo = cfg.get('github_repo')

    if owner and repo:
        remote_url = f"https://github.com/{owner}/{repo}.git"
        # Check current remote
        _, remotes, _ = run_git_cmd(['remote', '-v'])
        if 'origin' not in remotes:
            print(f"[*] Adding remote origin: {remote_url}")
            run_git_cmd(['remote', 'add', 'origin', remote_url])
        else:
            run_git_cmd(['remote', 'set-url', 'origin', remote_url])

    # Add all files
    print("[*] Staging files...")
    run_git_cmd(['add', '.'])

    # Commit
    print(f"[*] Committing: {commit_msg}")
    ok, out, err = run_git_cmd(['commit', '-m', commit_msg])
    if not ok and 'nothing to commit' in (out + err):
        print("[i] Nothing new to commit (working tree clean).")
    elif not ok:
        print(f"[!] Commit error: {err or out}")

    # Push
    if owner and repo:
        print(f"[*] Pushing to origin main...")
        ok, out, err = run_git_cmd(['push', '-u', 'origin', 'main'])
        if ok:
            print(f"[✓] Push successful to https://github.com/{owner}/{repo}!")
        else:
            print(f"[!] Push notice: {err or out}")
            print("    If authentication is needed, sign in via Git Credential Manager or GitHub Desktop.")

def main():
    cfg = load_config()
    if len(sys.argv) < 2:
        print("=" * 60)
        print("Crescent Islamic High School - GitHub Management Tool")
        print("=" * 60)
        print(f"Project Path : {SCRIPT_DIR}")
        print(f"GitHub Owner : {cfg.get('github_owner') or '(Not set yet)'}")
        print(f"GitHub Repo  : {cfg.get('github_repo')}")
        print(f"App Version  : {cfg.get('app_version')}")
        print("-" * 60)
        print("Available Commands:")
        print("  python github_sync.py status              -> Check config & GitHub connection")
        print("  python github_sync.py set-owner <owner>   -> Set your GitHub username")
        print("  python github_sync.py set-token <token>   -> Set GitHub personal access token")
        print("  python github_sync.py push \"Your message\" -> Commit and push all changes")
        print("=" * 60)
        return

    cmd = sys.argv[1].lower()

    if cmd == 'status':
        print(f"Checking status for {cfg.get('github_owner')}/{cfg.get('github_repo')}...")
        check_remote_status(cfg)
        git_ok, git_ver = check_git_installed()
        print(f"Local Git CLI: {git_ver if git_ok else 'Not installed'}")

    elif cmd == 'set-owner' and len(sys.argv) > 2:
        cfg['github_owner'] = sys.argv[2].strip()
        save_config(cfg)

    elif cmd == 'set-token' and len(sys.argv) > 2:
        cfg['github_token'] = sys.argv[2].strip()
        save_config(cfg)

    elif cmd == 'push':
        msg = sys.argv[2] if len(sys.argv) > 2 else "Update Crescent Seat Management School codebase"
        git_push_flow(msg)

    else:
        print(f"[!] Unknown command: {cmd}")

if __name__ == '__main__':
    main()
