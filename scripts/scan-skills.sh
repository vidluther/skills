#!/usr/bin/env bash
# Scan skills with SkillSpector (static analysis, no LLM).
#
# This is the single entry point for the local pre-commit gate (see AGENTS.md)
# and for CI (.github/workflows/checks.yml), so the pinned version and the gate
# can't drift apart.
#
# Usage:
#   scripts/scan-skills.sh                     # every skill git tracks or would commit (not ignored)
#   scripts/scan-skills.sh --all               # every skill under skills/, tracked or not
#   scripts/scan-skills.sh skills/<name> ...   # only these
#   scripts/scan-skills.sh -v ...              # list every finding, not just failing skills'
#
# Gate: a skill fails when SkillSpector exits non-zero, i.e. its risk score is
# above 50 ("DO NOT INSTALL") or the scan errored. Lower-scoring findings are
# reported but don't fail. Partial coverage doesn't fail either: most skills
# mention files that live in the repo they're used on, and SkillSpector counts
# those as missing references.
#
# Environment:
#   SKILLSPECTOR_REPORT_DIR  keep the per-skill JSON reports here (default: temp dir, deleted)
#   GITHUB_STEP_SUMMARY      set by GitHub Actions; a markdown summary is appended to it
#
# Needs jq, plus either `skillspector` on PATH or uv (runs the pinned version via uvx).

set -euo pipefail

SKILLSPECTOR_VERSION="2.13.2"
SKILLSPECTOR_COMMIT="abd82935b67f765a9541013c0866c6349251dcdf" # tag v2.13.2
SKILLSPECTOR_GIT="https://github.com/NVIDIA/SkillSpector.git"

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

usage() { sed -n '2,/^$/{s/^# \{0,1\}//;p;}' "$0"; }

verbose=0
all=0
targets=()
while [ $# -gt 0 ]; do
  case "$1" in
    -v | --verbose) verbose=1 ;;
    --all) all=1 ;;
    -h | --help) usage; exit 0 ;;
    -*) echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
    *) targets+=("${1%/}") ;;
  esac
  shift
done

if ! command -v jq >/dev/null 2>&1; then
  echo "error: jq not found." >&2
  exit 2
fi

if command -v skillspector >/dev/null 2>&1; then
  ss=(skillspector)
  have="$(skillspector --version 2>/dev/null | sed -n 's/.*v\([0-9][0-9.]*\).*/\1/p' | head -n1)"
  if [ "$have" != "$SKILLSPECTOR_VERSION" ]; then
    echo "warning: skillspector ${have:-(unknown version)} is on PATH, but CI pins $SKILLSPECTOR_VERSION. To match:" >&2
    echo "  uv tool install --force git+$SKILLSPECTOR_GIT@v$SKILLSPECTOR_VERSION" >&2
  fi
elif command -v uvx >/dev/null 2>&1; then
  ss=(uvx --quiet --from "git+$SKILLSPECTOR_GIT@$SKILLSPECTOR_COMMIT" skillspector)
else
  echo "error: need skillspector on PATH, or uv so it can run via uvx." >&2
  exit 2
fi

if [ ${#targets[@]} -eq 0 ]; then
  if [ "$all" -eq 1 ]; then
    for f in skills/*/SKILL.md; do
      [ -f "$f" ] && targets+=("${f%/SKILL.md}")
    done
  else
    # Tracked plus new-but-not-ignored, so a skill you're about to commit is included.
    while IFS= read -r f; do
      [ -f "$f" ] && targets+=("${f%/SKILL.md}")
    done < <(git ls-files --cached --others --exclude-standard -- ':(glob)skills/*/SKILL.md' | sort -u)
  fi
fi
if [ ${#targets[@]} -eq 0 ]; then
  echo "error: no skills found to scan." >&2
  exit 2
fi

scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT
report_dir="${SKILLSPECTOR_REPORT_DIR:-$scratch/reports}"
mkdir -p "$report_dir"
rows="$scratch/rows.md"
details="$scratch/details.md"
: >"$rows"
: >"$details"

findings_jq='.issues[] | "\(.severity) \(.id) \(.pattern) (\(.location.file):\(.location.start_line // "?"))"'

failed=0
total=0
for dir in "${targets[@]}"; do
  total=$((total + 1))
  name="$(basename "$dir")"
  if [ ! -f "$dir/SKILL.md" ]; then
    echo "FAIL  $name: no SKILL.md in $dir"
    echo "| $name | FAIL | – | no SKILL.md | – |" >>"$rows"
    failed=$((failed + 1))
    continue
  fi

  json="$report_dir/$name.json"
  log="$scratch/$name.log"
  rm -f "$json"
  rc=0
  "${ss[@]}" scan "$dir" --no-llm --format json --output "$json" >"$log" 2>&1 || rc=$?

  if [ ! -s "$json" ]; then
    echo "FAIL  $name: scan errored (exit $rc)"
    tail -n 20 "$log" | sed 's/^/      /'
    echo "| $name | FAIL | – | scan errored (exit $rc) | – |" >>"$rows"
    failed=$((failed + 1))
    continue
  fi

  status=PASS
  if [ "$rc" -ne 0 ]; then
    status=FAIL
    failed=$((failed + 1))
  fi
  IFS=$'\t' read -r score rec count < <(jq -r '[.risk_assessment.score, .risk_assessment.recommendation, (.issues | length)] | @tsv' "$json")
  printf '%-4s  %-32s score %3s  %-15s %s finding(s)\n' "$status" "$name" "$score" "$rec" "$count"
  if [ "$status" = FAIL ] || [ "$verbose" -eq 1 ]; then
    jq -r "$findings_jq" "$json" | sed 's/^/      /'
  fi

  echo "| $name | $status | $score | $rec | $count |" >>"$rows"
  if [ "$count" -gt 0 ]; then
    {
      echo "<details><summary>$name: $count finding(s)</summary>"
      echo
      jq -r "$findings_jq" "$json" | sed 's/^/- /'
      echo
      echo "</details>"
    } >>"$details"
  fi
done

if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
  {
    echo "## SkillSpector $SKILLSPECTOR_VERSION (static, no LLM)"
    echo
    echo "| Skill | Result | Score | Recommendation | Findings |"
    echo "| --- | --- | --- | --- | --- |"
    cat "$rows"
    echo
    cat "$details"
  } >>"$GITHUB_STEP_SUMMARY"
fi

echo
if [ "$failed" -gt 0 ]; then
  echo "$failed of $total skill(s) failed: risk score above 50, or the scan errored."
  exit 1
fi
echo "All $total skill(s) passed (risk score 50 or below). Run with -v to list every finding."
