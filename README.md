# zttato-platform

A multi-service growth/automation platform with Node.js and Python services, Docker-based infrastructure, and Cloudflare edge automation scripts.

## Import This Project to GitHub

Use this checklist when moving this repository into a GitHub repo (new or existing).

### 1) Prepare local repository metadata

```bash
# from repository root
cd /workspace/zttato-platform

# verify this is a git repository
git rev-parse --is-inside-work-tree

# check current branch and status
git branch --show-current
git status
```

### 2) Review sensitive files before pushing

Confirm secrets are **not** committed:

- API keys, access tokens, or Cloudflare credentials.
- Real production `.env` files.
- Private SSH keys and certificates.

Suggested checks:

```bash
# find likely env and key files
rg --files -g '*.env*' -g '*.pem' -g '*.key' -g '*.crt'

# quickly inspect gitignored files
cat .gitignore
```

If sensitive data is present in commit history, rewrite history before publishing.

### 3) Create GitHub repository

1. Open GitHub and create a new repository.
2. Choose repository visibility (public/private).
3. Do **not** initialize with README/license if this repo is already initialized locally.

### 4) Add remote and push

```bash
# add GitHub remote (replace URL)
git remote add origin git@github.com:<org-or-user>/zttato-platform.git

# verify remote
git remote -v

# push current branch and set upstream
git push -u origin "$(git branch --show-current)"
```

If `origin` already exists:

```bash
git remote set-url origin git@github.com:<org-or-user>/zttato-platform.git
git push -u origin "$(git branch --show-current)"
```

### 5) Optional: push all branches and tags

```bash
git push --all origin
git push --tags origin
```

## Recommended GitHub Repository Settings

After import, configure:

- **Branch protection** for `main` (PR required, status checks required).
- **Actions permissions** (least privilege, required secrets only).
- **Dependabot alerts** and security updates.
- **CODEOWNERS** for review routing.

## Project Structure

```text
.
├── docker-compose.yml
├── start-zttato.sh
├── cloudflare-devops/
├── infrastructure/
├── scripts/
└── services/
```

## Local Validation Commands

```bash
# shell scripts syntax check
while IFS= read -r f; do bash -n "$f"; done < <(rg --files -g '*.sh')

# python syntax check
python -m compileall services

# package.json validation
while IFS= read -r f; do python -m json.tool "$f" >/dev/null; done < <(rg --files -g 'package.json')
```

## Troubleshooting Import

- `Permission denied (publickey)`: add your SSH key to GitHub or use HTTPS remote.
- `remote origin already exists`: use `git remote set-url origin ...`.
- `large file rejected`: use Git LFS and re-commit large assets.
- `push rejected/non-fast-forward`: run `git pull --rebase origin <branch>` then push again.
