#!/usr/bin/env bash
# Regenerate the GitButler skill and steering text from the installed `but` CLI
# so agents always get guidance that matches the binary they run.
#
# - skills/gitbutler/          <- `but skill install`
# - gitbutler-steering.md      <- `but agent setup --print` + gitbutler-steering.extra.md
#   (the wizard's opt-in sections; --print only emits the defaults)
#
# Regenerates when the version stamp in SKILL.md differs from `but --version`,
# when a generated file is missing, or when the extra file changed. Then syncs the
# steering block into the Codex and OpenCode instruction files (no-op when current).
# Pass --force to regenerate anyway.
#
# Called by setup.sh, the Claude Code SessionStart hook, and the OpenCode
# plugin (~/.config/opencode/plugins/gitbutler-skill-refresh.js).

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_DIR="$REPO_DIR/skills/gitbutler"
STEERING="$REPO_DIR/gitbutler-steering.md"
STEERING_EXTRA="$REPO_DIR/gitbutler-steering.extra.md"
END_MARKER='<!-- gitbutler-agent-setup:end -->'

command -v but >/dev/null 2>&1 || exit 0

cli="$(but --version | awk '{print $2}')"
have="$(sed -n 's/^version: //p' "$SKILL_DIR/SKILL.md" 2>/dev/null | head -n 1)"
force=false
[ "${1:-}" = "--force" ] && force=true

if $force || [ "$cli" != "$have" ]; then
  but skill install --global --path "$SKILL_DIR" </dev/null >/dev/null
  echo "refreshed gitbutler skill: ${have:-none} -> $cli"
fi

if $force || [ "$cli" != "$have" ] || [ ! -f "$STEERING" ] \
  || { [ -f "$STEERING_EXTRA" ] && [ "$STEERING_EXTRA" -nt "$STEERING" ]; }; then
  tmp="$(mktemp)"
  {
    but agent setup --print | grep -vF "$END_MARKER"
    if [ -f "$STEERING_EXTRA" ]; then
      cat "$STEERING_EXTRA"
    fi
    echo "$END_MARKER"
  } > "$tmp"
  if cmp -s "$tmp" "$STEERING"; then
    rm "$tmp"
    touch "$STEERING"
  else
    mv "$tmp" "$STEERING"
    echo "refreshed gitbutler steering ($cli)"
  fi
fi

# Replace the marker-delimited steering block in an instruction file, appending
# it (or creating the file) when absent. No-op when already up to date.
inject_steering() {
  local file="$1"
  if [ -L "$file" ]; then
    echo "skip     $file (symlink; likely dotfile-managed — update it yourself)"
    return
  fi
  mkdir -p "$(dirname "$file")"
  if [ ! -e "$file" ]; then
    cp "$STEERING" "$file"
    echo "created  $file (steering block)"
    return
  fi
  if grep -q 'gitbutler-agent-setup:start' "$file"; then
    local tmp
    tmp="$(mktemp)"
    awk -v src="$STEERING" '
      /<!-- gitbutler-agent-setup:start -->/ {
        while ((getline line < src) > 0) print line
        close(src)
        skipping = 1
        next
      }
      /<!-- gitbutler-agent-setup:end -->/ { if (skipping) { skipping = 0; next } }
      !skipping { print }
    ' "$file" > "$tmp"
    if cmp -s "$tmp" "$file"; then
      rm "$tmp"
    else
      mv "$tmp" "$file"
      echo "updated  $file (steering block)"
    fi
  else
    { echo; cat "$STEERING"; } >> "$file"
    echo "appended $file (steering block)"
  fi
}

inject_steering "$HOME/.codex/AGENTS.md"
inject_steering "$HOME/.config/opencode/AGENTS.md"
