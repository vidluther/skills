#!/usr/bin/env bash
# Sabu vendor check — review what changed upstream for a vendored (third-party)
# skill, so you can hand-merge the bits you want.
#
# Why this is READ-ONLY: a skill is instructions an agent executes while holding
# real tools (shell, file edits, MCP). A vendored skill is therefore third-party
# *code you run*, and auto-pulling upstream is an unattended supply-chain channel.
# So this script never writes into skills/ — it only fetches upstream, shows you
# the diff, and scans the candidate. YOU read it, merge by hand, and bump the
# provenance fields. (See README "Security" for the full rationale.)
#
# Usage:
#   ./update-thirdparty-skills.sh              # check every skill that has a `source:` field
#   ./update-thirdparty-skills.sh shadcn-ui    # check just the named skill(s)
#
# A skill is "vendored" iff its SKILL.md frontmatter has a top-level `source:`.
# Recognised provenance fields (all flat, top-level, so `rg '^source:'` audits):
#   source:        clone-able upstream repo URL          (required)
#   source_path:   path to the skill within that repo    (optional; default repo root)
#   upstream_ref:  commit/tag you last reconciled against (optional; baseline if absent)
#   last_reviewed: date you last reviewed the diff        (informational)

set -euo pipefail

SABU_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$SABU_DIR/skills"

TMP_ROOT="$(mktemp -d)"
cleanup() { rm -rf "$TMP_ROOT"; }
trap cleanup EXIT

# Read a flat top-level scalar from the first YAML frontmatter block of a file.
# Strips a trailing " # comment" and surrounding quotes. Always exits 0.
frontmatter_field() {
  local file="$1" key="$2"
  sed -n '/^---$/,/^---$/p' "$file" 2>/dev/null \
    | grep -m1 "^${key}:" \
    | sed -E "s/^${key}:[[:space:]]*//; s/[[:space:]]+#.*$//; s/^['\"]//; s/['\"]\$//" \
    || true
}

check_skill() {
  local name="$1" explicit="$2"
  local skill_dir="$SKILLS_DIR/$name"
  local skill_md="$skill_dir/SKILL.md"

  if [ ! -f "$skill_md" ]; then
    [ "$explicit" = "1" ] && echo "skip   $name: no SKILL.md at $skill_md"
    return 0
  fi

  local source source_path upstream_ref
  source="$(frontmatter_field "$skill_md" source)"
  if [ -z "$source" ]; then
    # First-party skill (no provenance recorded) — nothing to check.
    [ "$explicit" = "1" ] && echo "skip   $name: no \`source:\` field (first-party, or provenance not recorded)"
    return 0
  fi
  source_path="$(frontmatter_field "$skill_md" source_path)"
  upstream_ref="$(frontmatter_field "$skill_md" upstream_ref)"
  local pathspec="${source_path:-.}"

  echo "=== $name ==="
  echo "source:       $source"
  echo "source_path:  ${source_path:-<repo root>}"
  echo "upstream_ref: ${upstream_ref:-<none recorded>}"
  echo

  # Blobless partial clone: full commit graph (so ranges work) without pulling
  # every blob in history. Cheap even for large monorepos.
  local tmp
  tmp="$(mktemp -d "$TMP_ROOT/${name}.XXXXXX")"
  if ! git clone --quiet --filter=blob:none --no-tags "$source" "$tmp"; then
    echo "  error: could not clone $source"
    echo
    return 0
  fi

  local head_sha
  head_sha="$(git -C "$tmp" rev-parse HEAD)"

  # 1) What changed upstream since you last reconciled — the diff you review.
  if [ -n "$upstream_ref" ]; then
    if git -C "$tmp" cat-file -e "${upstream_ref}^{commit}" 2>/dev/null; then
      echo "  --- upstream commits  ${upstream_ref}..HEAD  ($pathspec) ---"
      git -C "$tmp" --no-pager log --oneline "${upstream_ref}..HEAD" -- "$pathspec" || true
      echo
      echo "  --- upstream diff  ${upstream_ref}..HEAD  ($pathspec) ---"
      git -C "$tmp" --no-pager diff "${upstream_ref}..HEAD" -- "$pathspec" || true
    else
      echo "  warning: upstream_ref '$upstream_ref' not found upstream (force-push/rebase, or wrong ref)."
      echo "           Falling back to fork-vs-upstream comparison below."
    fi
  else
    echo "  No upstream_ref recorded yet — first reconciliation. Review the fork-vs-upstream"
    echo "  comparison below, then record the baseline ref printed at the end."
  fi
  echo

  # 2) How far your fork has diverged from upstream HEAD (context for merging).
  echo "  --- your fork vs upstream HEAD (summary) ---"
  git --no-pager diff --no-index --stat -- "$tmp/$pathspec" "$skill_dir" || true
  echo

  # 3) Safety gate: scan the upstream candidate you're about to pull from.
  echo "  --- skillspector scan (upstream candidate) ---"
  if command -v skillspector >/dev/null 2>&1; then
    if skillspector scan --no-llm "$tmp/$pathspec"; then
      echo "  skillspector: PASS"
    else
      echo "  skillspector: REVIEW — non-zero exit; read findings above before merging."
    fi
  else
    echo "  skillspector not on PATH — scan manually: skillspector scan --no-llm $tmp/$pathspec"
    echo "  (note: $tmp is removed when this script exits)"
  fi
  echo

  # 4) What to record after you've reviewed + merged by hand.
  echo "  After review + hand-merge, update skills/$name/SKILL.md frontmatter:"
  echo "    upstream_ref: $head_sha"
  echo "    last_reviewed: $(date +%F)"
  echo "  Then run ./setup.sh."
  echo
}

main() {
  if [ ! -d "$SKILLS_DIR" ]; then
    echo "error: $SKILLS_DIR does not exist" >&2
    exit 1
  fi

  if [ "$#" -gt 0 ]; then
    for name in "$@"; do
      check_skill "$name" 1
    done
  else
    for skill_path in "$SKILLS_DIR"/*/; do
      check_skill "$(basename "$skill_path")" 0
    done
  fi
}

main "$@"
