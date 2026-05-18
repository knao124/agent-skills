#!/usr/bin/env bash
set -euo pipefail

skip_gh=false
if [[ "${1:-}" == "--skip-gh" ]]; then
  skip_gh=true
  shift
fi

if [[ "$#" -gt 0 ]]; then
  echo "usage: scripts/validate-skills.sh [--skip-gh]" >&2
  exit 2
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

skill_dirs=()
if [[ -d "$repo_root/skills" ]]; then
  while IFS= read -r skill_md; do
    skill_dirs+=("$(dirname "$skill_md")")
  done < <(find "$repo_root/skills" -type f -name SKILL.md | sort)
fi

if [[ "${#skill_dirs[@]}" -eq 0 ]]; then
  echo "No skills found under $repo_root/skills" >&2
  exit 1
fi

if command -v agentskills >/dev/null 2>&1; then
  validator=(agentskills validate)
elif command -v skills-ref >/dev/null 2>&1; then
  validator=(skills-ref validate)
else
  echo "Missing Agent Skills validator." >&2
  echo "Install it with: python -m pip install skills-ref" >&2
  exit 127
fi

for skill_dir in "${skill_dirs[@]}"; do
  echo "Validating $skill_dir"
  "${validator[@]}" "$skill_dir"
done

python3 "$repo_root/scripts/check-evals.py"

if [[ "$skip_gh" == false ]]; then
  if ! command -v gh >/dev/null 2>&1; then
    echo "Missing GitHub CLI: gh" >&2
    exit 127
  fi

  if ! gh skill --help >/dev/null 2>&1; then
    echo "GitHub CLI does not provide gh skill. Install gh 2.90.0 or newer." >&2
    exit 127
  fi

  gh skill publish "$repo_root" --dry-run
fi
