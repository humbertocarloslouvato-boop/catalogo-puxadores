#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated setup of cloud backup for Continuous Memory Layer.

This script will:
  1. Check git/ssh
  2. Generate SSH key if missing
  3. Show instructions to add SSH key to GitHub/GitLab
  4. Optionally create private repo via GitHub CLI or API token
  5. Clone/link cloud repo and push initial memory files
"""

import argparse
import os
import platform
import subprocess
import sys
import urllib.request
import json
from pathlib import Path


HOME = Path.home()
SSH_DIR = HOME / ".ssh"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
PROJECT_NAME = PROJECT_ROOT.name
CLOUD_DIR = HOME / ".continuous-memory" / PROJECT_NAME


def run(cmd, check=True, capture=True):
    print(f"\n[RUN] {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=capture, text=True)
    if result.returncode != 0 and check:
        print("STDERR:", result.stderr)
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")
    return result


def check_git_ssh():
    print("\n[CHECK] Verifying git and ssh...")
    run(["git", "--version"])
    run(["ssh", "-V"], check=False)
    print("[OK] git and ssh available")


def ensure_ssh_key():
    print("\n[CHECK] SSH key...")
    SSH_DIR.mkdir(parents=True, exist_ok=True)
    key_file = SSH_DIR / "id_rsa"
    pub_file = key_file.with_suffix(".pub")

    if key_file.exists() and pub_file.exists():
        print(f"[OK] SSH key already exists: {key_file}")
    else:
        print("[GEN] Generating SSH key (no passphrase)...")
        run([
            "ssh-keygen", "-t", "rsa", "-b", "4096",
            "-f", str(key_file), "-N", "", "-C", f"continuous-memory@{PROJECT_NAME}"
        ])
        print(f"[OK] Generated {key_file}")

    pub_key = pub_file.read_text(encoding="utf-8").strip()
    print(f"\n{'='*60}")
    print("PUBLIC SSH KEY (copy the entire line below):")
    print(f"{'='*60}")
    print(pub_key)
    print(f"{'='*60}\n")
    print("INSTRUCTIONS:")
    print("1. Go to https://github.com/settings/keys")
    print("2. Click 'New SSH key'")
    print("3. Title: continuous-memory")
    print("4. Paste the key above")
    print("5. Click 'Add SSH key'")
    print("6. If asked for authentication, confirm with your GitHub password/2FA\n")
    return pub_key


def test_ssh_github():
    print("[TEST] Testing SSH connection to GitHub...")
    result = run(["ssh", "-T", "git@github.com"], check=False)
    if "successfully authenticated" in result.stderr or result.returncode == 1:
        print("[OK] SSH connection to GitHub works")
        return True
    else:
        print("[WARN] SSH connection failed. Did you add the key to GitHub?")
        print(result.stderr)
        return False


def install_gh_cli():
    """Try to install GitHub CLI. Returns True if available."""
    print("\n[CHECK] GitHub CLI (gh)...")
    gh = shutil.which("gh")
    if gh:
        print(f"[OK] gh already installed: {gh}")
        return True

    print("[INFO] gh CLI not found. You can install it from:")
    print("       https://github.com/cli/cli/releases")
    print("       Or use the GitHub API token method below.")
    return False


def create_repo_via_gh(repo_name, private=True):
    print(f"\n[ACTION] Creating private repo '{repo_name}' via gh CLI...")
    visibility = "--private" if private else "--public"
    result = run([
        "gh", "repo", "create", repo_name,
        visibility, "--confirm", "--description",
        f"Continuous memory backup for {PROJECT_NAME}"
    ], check=False)
    if result.returncode == 0:
        print("[OK] Repository created")
        return f"git@github.com:{get_gh_username()}/{repo_name}.git"
    else:
        print("[ERROR] Failed to create repo via gh:", result.stderr)
        return None


def get_gh_username():
    result = run(["gh", "api", "user", "--jq", ".login"], check=False)
    if result.returncode == 0:
        return result.stdout.strip()
    return "YOUR_USERNAME"


def create_repo_via_api(token, repo_name, private=True):
    print(f"\n[ACTION] Creating private repo '{repo_name}' via GitHub API...")
    data = json.dumps({
        "name": repo_name,
        "private": private,
        "description": f"Continuous memory backup for {PROJECT_NAME}",
        "auto_init": False
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.github.com/user/repos",
        data=data,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as resp:
            repo_info = json.loads(resp.read().decode("utf-8"))
            ssh_url = repo_info["ssh_url"]
            print(f"[OK] Created: {repo_info['html_url']}")
            return ssh_url
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"[ERROR] API error {e.code}: {body}")
        return None


def setup_local_cloud_repo(repo_url):
    print(f"\n[SETUP] Configuring local cloud mirror at {CLOUD_DIR}...")
    CLOUD_DIR.parent.mkdir(parents=True, exist_ok=True)

    if (CLOUD_DIR / ".git").exists():
        print(f"[INFO] {CLOUD_DIR} already a git repo")
    else:
        if CLOUD_DIR.exists() and any(CLOUD_DIR.iterdir()):
            print(f"[WARN] {CLOUD_DIR} not empty, moving aside")
            backup = CLOUD_DIR.with_name(CLOUD_DIR.name + "_backup")
            CLOUD_DIR.rename(backup)
        run(["git", "clone", repo_url, str(CLOUD_DIR)])

    # Create symlinks for memory directories inside cloud repo
    local_memory = PROJECT_ROOT / "memory"
    cloud_memory = CLOUD_DIR / "memory"
    if not cloud_memory.exists():
        if os.name == "nt":
            import ctypes
            # Windows junction/symlink needs admin or dev mode; try symlink anyway
            try:
                cloud_memory.symlink_to(local_memory.resolve(), target_is_directory=True)
            except OSError:
                print("[WARN] Could not create symlink on Windows. Using copy strategy.")
                return "copy"
        else:
            cloud_memory.symlink_to(local_memory.resolve(), target_is_directory=True)
        print(f"[LINK] {cloud_memory} -> {local_memory}")

    kimi_memory = PROJECT_ROOT / ".kimi-code" / "memory"
    cloud_kimi = CLOUD_DIR / ".kimi-code" / "memory"
    cloud_kimi.parent.mkdir(parents=True, exist_ok=True)
    if not cloud_kimi.exists():
        if os.name == "nt":
            try:
                cloud_kimi.symlink_to(kimi_memory.resolve(), target_is_directory=True)
            except OSError:
                print("[WARN] Could not create symlink on Windows. Using copy strategy.")
                return "copy"
        else:
            cloud_kimi.symlink_to(kimi_memory.resolve(), target_is_directory=True)
        print(f"[LINK] {cloud_kimi} -> {kimi_memory}")

    return "symlink"


def push_initial_memory(strategy="symlink"):
    print("\n[PUSH] Sending initial memory files to cloud...")
    cd_cmd = ["git", "-C", str(CLOUD_DIR)]

    if strategy == "copy":
        # Copy instead of symlink
        import shutil
        src_memory = PROJECT_ROOT / "memory"
        dst_memory = CLOUD_DIR / "memory"
        if dst_memory.exists():
            shutil.rmtree(dst_memory)
        shutil.copytree(src_memory, dst_memory)

        src_kimi = PROJECT_ROOT / ".kimi-code" / "memory"
        dst_kimi = CLOUD_DIR / ".kimi-code" / "memory"
        if dst_kimi.exists():
            shutil.rmtree(dst_kimi)
        shutil.copytree(src_kimi, dst_kimi)
        print("[COPY] Memory files copied to cloud dir")

    run(cd_cmd + ["add", "-A"])
    result = run(cd_cmd + ["diff", "--cached", "--quiet"], check=False)
    if result.returncode == 0:
        print("[INFO] No changes to commit")
    else:
        timestamp = subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], capture_output=True, text=True).stdout.strip()
        run(cd_cmd + ["commit", "-m", f"[memory-backup] initial sync {timestamp}"])
        run(cd_cmd + ["push", "origin", "HEAD"])
        print(f"[OK] Initial memory backup pushed at {timestamp}")


def main():
    parser = argparse.ArgumentParser(description="Setup cloud backup for Continuous Memory Layer")
    parser.add_argument("--repo-name", default=f"{PROJECT_NAME}-memory", help="Cloud repo name")
    parser.add_argument("--token", help="GitHub Personal Access Token (alternative to gh CLI)")
    parser.add_argument("--repo-url", help="Existing repo URL (skip creation)")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print("CONTINUOUS MEMORY LAYER — Cloud Backup Setup")
    print(f"Project: {PROJECT_NAME}")
    print(f"{'='*60}\n")

    check_git_ssh()
    ensure_ssh_key()

    if args.repo_url:
        repo_url = args.repo_url
        print(f"\n[INFO] Using provided repo: {repo_url}")
    else:
        if not test_ssh_github():
            instructions_file = PROJECT_ROOT / "CLOUD_BACKUP_INSTRUCTIONS.md"
            pub_key = (SSH_DIR / "id_rsa.pub").read_text(encoding="utf-8").strip()
            instructions = f"""# Cloud Backup Setup Instructions

Your SSH key has been generated but needs to be added to GitHub before the automated setup can continue.

## Step 1: Add SSH key to GitHub

1. Go to https://github.com/settings/keys
2. Click **New SSH key**
3. Title: `continuous-memory`
4. Paste this entire key:

```
{pub_key}
```

5. Click **Add SSH key**
6. Confirm with password/2FA if asked

## Step 2: Create private repository

Option A — GitHub website:
- Go to https://github.com/new
- Repository name: `ruflo-memory`
- Select **Private**
- Do NOT initialize with README
- Click **Create repository**

Option B — GitHub CLI (if installed):
```bash
gh auth login
gh repo create ruflo-memory --private --confirm
```

## Step 3: Continue automated setup

After completing steps 1 and 2, run one of:

```bash
# If you created the repo manually, pass the SSH URL:
python .kimi-code/skills/continuous-memory/scripts/setup_cloud_backup.py \\
  --repo-url git@github.com:SEU_USUARIO/ruflo-memory.git

# Or if you have a GitHub token:
python .kimi-code/skills/continuous-memory/scripts/setup_cloud_backup.py \\
  --token SEU_TOKEN_AQUI
```

Replace `SEU_USUARIO` with your GitHub username.
"""
            instructions_file.write_text(instructions, encoding="utf-8")
            print(f"\n[INFO] Instructions saved to: {instructions_file}")
            print("[PAUSE] Please follow the instructions above, then rerun this script.")
            sys.exit(0)

        repo_url = None
        if shutil.which("gh"):
            print("\n[INFO] GitHub CLI detected. We can create the repo automatically.")
            print("Make sure you are logged in: gh auth login")
            repo_url = create_repo_via_gh(args.repo_name)
        elif args.token:
            repo_url = create_repo_via_api(args.token, args.repo_name)
        else:
            print("\n[OPTIONS] Choose how to create the private repo:")
            print("1. Install gh CLI and run: gh auth login")
            print("2. Provide a GitHub token: --token YOUR_TOKEN")
            print("3. Create the repo manually and rerun with: --repo-url git@github.com:USER/REPO.git")
            sys.exit(0)

    if not repo_url:
        print("[ERROR] Could not determine repo URL")
        sys.exit(1)

    strategy = setup_local_cloud_repo(repo_url)
    push_initial_memory(strategy)

    print("\n" + "="*60)
    print("SETUP COMPLETE")
    print("="*60)
    print(f"Cloud repo: {repo_url}")
    print(f"Local mirror: {CLOUD_DIR}")
    print("\nTo schedule auto-backup, add this to crontab/Task Scheduler:")
    script_path = Path(__file__).resolve().parent / "auto_backup.sh"
    print(f"  bash \"{script_path}\"")
    print("\n[OK] Memory will now be backed up automatically.")


if __name__ == "__main__":
    import shutil
    main()
