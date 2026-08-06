#!/usr/bin/env bash
# Skills setup — wire skills (and, in future, hooks/configs) into the locations
# agent tooling reads.
#
# Destinations:
# - $AGENT_SKILLS_DIR ($HOME/.agents/skills) — universal location for the AGENTS.md
#   convention; tools that follow it (or future hooks/configs this repo adds) read from here.
# - $CLAUDE_SKILLS_DIR ($HOME/.claude/skills/<name>) — Claude Code-specific. Each skill
#   needs its own entry in this directory because that's where Claude Code discovers them.
# - $GEMINI_SKILLS_DIR ($HOME/.gemini/antigravity/skills/<name>) — Gemini Antigravity.
#   Same per-skill shape as Claude Code; Antigravity enumerates this directory.
#
# Idempotent: safe to re-run after adding, removing, or renaming skills.
# - Replaces existing symlinks pointing at stale targets (e.g. an older clone path).
# - Skips real directories at the target (won't clobber); reports them.
# - Reports dangling symlinks in each per-skill destination.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$REPO_DIR/skills"

AGENTS_DIR="$HOME/.agents"
AGENT_SKILLS_DIR="$AGENTS_DIR/skills"
CLAUDE_SKILLS_DIR="$HOME/.claude/skills"
GEMINI_SKILLS_DIR="$HOME/.gemini/antigravity/skills"

if [ ! -d "$SKILLS_DIR" ]; then
  echo "error: $SKILLS_DIR does not exist" >&2
  exit 1
fi

# Ensure $AGENTS_DIR exists and is writable. If it's currently a symlink (e.g. a stow
# link from dotfiles), surface that and bail — the user needs to decide what to do.
if [ -L "$AGENTS_DIR" ]; then
  echo "error: $AGENTS_DIR is a symlink (-> $(readlink "$AGENTS_DIR"))." >&2
  echo "       Likely managed by stow or another dotfile manager." >&2
  echo "       Remove or replace it before re-running setup.sh." >&2
  exit 1
fi
mkdir -p "$AGENTS_DIR"
mkdir -p "$CLAUDE_SKILLS_DIR"
mkdir -p "$GEMINI_SKILLS_DIR"

# 1) Universal location: $AGENT_SKILLS_DIR is one symlink to this repo's skills/.
# Single parent symlink (rather than per-skill) keeps the AGENTS.md path
# uniform — anything added under skills/ shows up automatically.
if [ -L "$AGENT_SKILLS_DIR" ]; then
  current="$(readlink "$AGENT_SKILLS_DIR")"
  if [ "$current" != "$SKILLS_DIR" ]; then
    rm "$AGENT_SKILLS_DIR"
    ln -s "$SKILLS_DIR" "$AGENT_SKILLS_DIR"
    echo "replaced $AGENT_SKILLS_DIR (was -> $current)"
  fi
elif [ -e "$AGENT_SKILLS_DIR" ]; then
  echo "skip     $AGENT_SKILLS_DIR (real directory exists; not overwriting)"
else
  ln -s "$SKILLS_DIR" "$AGENT_SKILLS_DIR"
  echo "linked   $AGENT_SKILLS_DIR -> $SKILLS_DIR"
fi

# 2) Per-skill destinations: one symlink per skill under each target dir.
# Claude Code and Gemini Antigravity both enumerate their skills directory, so
# each skill needs its own entry rather than a single parent symlink.
link_skills_into() {
  local target_dir="$1" label="$2"
  local linked=0 replaced=0 skipped=0
  local skill src link current

  for skill_path in "$SKILLS_DIR"/*/; do
    skill="$(basename "$skill_path")"
    src="${skill_path%/}"
    link="$target_dir/$skill"

    if [ -L "$link" ]; then
      current="$(readlink "$link")"
      if [ "$current" = "$src" ]; then
        continue
      fi
      rm "$link"
      ln -s "$src" "$link"
      echo "replaced $link (was -> $current)"
      replaced=$((replaced + 1))
    elif [ -e "$link" ]; then
      echo "skip     $link (real directory exists; not overwriting)"
      skipped=$((skipped + 1))
    else
      ln -s "$src" "$link"
      echo "linked   $link"
      linked=$((linked + 1))
    fi
  done

  echo "$label: $linked new symlinks, $replaced replaced, $skipped skipped (real dirs)."
}

# 3) Report dangling symlinks in a per-skill destination (point at paths
# that no longer exist — usually leftovers from a previous setup).
report_dangling() {
  local target_dir="$1"
  local dangling=() entry
  for entry in "$target_dir"/*; do
    [ -L "$entry" ] || continue
    [ -e "$entry" ] && continue
    dangling+=("$(basename "$entry") -> $(readlink "$entry")")
  done

  if [ "${#dangling[@]}" -gt 0 ]; then
    echo
    echo "Dangling symlinks in $target_dir (point at non-existent paths):"
    for d in "${dangling[@]}"; do
      echo "  $d"
    done
    echo "Remove these manually if they're stale: rm $target_dir/<name>"
  fi
}

link_skills_into "$CLAUDE_SKILLS_DIR" "claude"
link_skills_into "$GEMINI_SKILLS_DIR" "antigravity"

report_dangling "$CLAUDE_SKILLS_DIR"
report_dangling "$GEMINI_SKILLS_DIR"

echo
echo "Skills setup complete."
