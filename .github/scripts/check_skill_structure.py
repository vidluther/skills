# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml==6.0.3"]
# ///
"""Check that every git-tracked skill has the shape AGENTS.md describes.

    uv run --script .github/scripts/check_skill_structure.py

Checks:
- SKILL.md has YAML frontmatter; `name` matches the directory; `description` is set.
- Vendored skills (frontmatter has `source:`) also set `upstream_ref` and `last_reviewed`.
- agents/openai.yaml exists, parses, and sets interface.display_name,
  short_description, and a default_prompt that mentions `$<name>`.
- Relative markdown links in tracked .md files point at tracked files.

Only files git tracks or would commit count, so a local run matches CI:
gitignored skills (aws, twg, generated gitbutler files) are out of scope.
"""

from __future__ import annotations

import posixpath
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

import yaml

ROOT = Path(__file__).resolve().parents[2]
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
LINK = re.compile(r"\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+[\"'][^)]*[\"'])?\s*\)")
INLINE_CODE = re.compile(r"`[^`]*`")
URL_SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*:", re.I)
FENCE = re.compile(r"^\s*(```|~~~)")

errors: list[str] = []


def error(where: str | Path, message: str) -> None:
    errors.append(f"{where}: {message}")


def tracked_files() -> list[str]:
    """Tracked files plus new, not-ignored ones: what a commit would contain."""
    out = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return sorted({p for p in out.split("\0") if p and (ROOT / p).is_file()})


def load_yaml(text: str, where: str) -> object | None:
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as exc:
        error(where, f"not valid YAML: {exc}")
        return None


def check_skill(skill_md: str, tracked: set[str]) -> None:
    skill_dir = posixpath.dirname(skill_md)
    dir_name = posixpath.basename(skill_dir)
    text = (ROOT / skill_md).read_text(encoding="utf-8")

    match = FRONTMATTER.match(text)
    if not match:
        error(skill_md, "no YAML frontmatter (a --- block at the top of the file)")
        return
    meta = load_yaml(match.group(1), f"{skill_md} frontmatter")
    if meta is None:
        return
    if not isinstance(meta, dict):
        error(skill_md, "frontmatter must be a mapping")
        return

    name = meta.get("name")
    if name != dir_name:
        error(skill_md, f"name {name!r} must match the directory name {dir_name!r}")
    description = meta.get("description")
    if not isinstance(description, str) or not description.strip():
        error(skill_md, "description is missing or empty")
    if "source" in meta:
        for field in ("upstream_ref", "last_reviewed"):
            if not meta.get(field):
                error(skill_md, f"vendored skill (has source:) is missing {field}:")

    openai_yaml = f"{skill_dir}/agents/openai.yaml"
    if openai_yaml not in tracked:
        error(openai_yaml, "missing; every skill needs agents/openai.yaml")
        return
    data = load_yaml((ROOT / openai_yaml).read_text(encoding="utf-8"), openai_yaml)
    if data is None:
        return
    interface = data.get("interface") if isinstance(data, dict) else None
    if not isinstance(interface, dict):
        error(openai_yaml, "needs an interface: mapping")
        return
    for key in ("display_name", "short_description", "default_prompt"):
        value = interface.get(key)
        if not isinstance(value, str) or not value.strip():
            error(openai_yaml, f"interface.{key} is missing or empty")
    prompt = interface.get("default_prompt")
    if isinstance(prompt, str) and f"${dir_name}" not in prompt:
        error(openai_yaml, f"interface.default_prompt should mention ${dir_name}")


def check_links(md_file: str, tracked: set[str], tracked_dirs: set[str]) -> None:
    in_fence = False
    lines = (ROOT / md_file).read_text(encoding="utf-8").splitlines()
    for lineno, line in enumerate(lines, 1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for target in LINK.findall(INLINE_CODE.sub("", line)):
            if URL_SCHEME.match(target) or target.startswith(("#", "/")):
                continue
            path = unquote(target.split("#", 1)[0].split("?", 1)[0])
            if not path:
                continue
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(md_file), path))
            if resolved.startswith("../"):
                error(f"{md_file}:{lineno}", f"link points outside the repo: {target}")
            elif resolved not in tracked and resolved not in tracked_dirs:
                error(f"{md_file}:{lineno}", f"link target is not a tracked file: {target}")


def main() -> int:
    files = tracked_files()
    tracked = set(files)
    tracked_dirs = {posixpath.dirname(p) for p in files}
    for p in list(tracked_dirs):
        while p:
            p = posixpath.dirname(p)
            tracked_dirs.add(p)

    skills = sorted(p for p in files if re.fullmatch(r"skills/[^/]+/SKILL\.md", p))
    for skill_md in skills:
        check_skill(skill_md, tracked)

    for p in files:
        if re.fullmatch(r"skills/[^/]+/agents/openai\.yaml", p) and not p.startswith(
            tuple(posixpath.dirname(s) + "/" for s in skills)
        ):
            # Skills whose SKILL.md is generated and gitignored (gitbutler): YAML must still parse.
            load_yaml((ROOT / p).read_text(encoding="utf-8"), p)

    markdown = [p for p in files if p.endswith(".md")]
    for md_file in markdown:
        check_links(md_file, tracked, tracked_dirs)

    if errors:
        print(f"{len(errors)} problem(s):")
        for line in errors:
            print(f"  {line}")
        return 1
    print(f"OK: {len(skills)} skills, {len(markdown)} markdown files checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
