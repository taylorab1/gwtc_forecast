#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ ! -d "${REPO_ROOT}/.git" ]]; then
  echo "No .git directory found; skipping pre-commit hook installation."
  exit 0
fi
cat > "${REPO_ROOT}/.git/hooks/pre-commit" <<'HOOK'
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "${ROOT}"
if command -v conda >/dev/null 2>&1; then
  conda run --no-capture-output -n gwtc_forecast gwtc-forecast audit-repo
else
  echo "ERROR: conda unavailable; cannot run repository data guard." >&2
  exit 1
fi
HOOK
chmod +x "${REPO_ROOT}/.git/hooks/pre-commit"
echo "Installed .git/hooks/pre-commit repository data guard."
