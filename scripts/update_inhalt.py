"""Regenerate docs/inhalt.md — a linked table of contents over every Markdown file.

Run from the repo root whenever Markdown files are added, moved or renamed:

    python3 scripts/update_inhalt.py
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT = REPO_ROOT / "docs" / "inhalt.md"
SKIP_DIRS = {".git", ".claude", ".venv", "node_modules", "cdk.out", "dist", "__pycache__",
             ".pytest_cache", ".ruff_cache"}
# section order in the generated document; everything else lands under "Weitere"
SECTIONS = ["<root>", "docs", "tag-1", "tag-2", "tag-3", "infrastructure", "shared", "scripts"]


def first_heading(path: Path) -> str:
    """Return the first Markdown heading (frontmatter-aware), or the file name."""
    lines = path.read_text(encoding="utf-8").splitlines()
    in_frontmatter = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if i == 0 and stripped == "---":
            in_frontmatter = True
            continue
        if in_frontmatter:
            if stripped == "---":
                in_frontmatter = False
            continue
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return path.name


def collect() -> dict[str, list[Path]]:
    grouped: dict[str, list[Path]] = {name: [] for name in SECTIONS}
    grouped["Weitere"] = []
    for path in sorted(REPO_ROOT.rglob("*.md")):
        rel = path.relative_to(REPO_ROOT)
        if any(part in SKIP_DIRS for part in rel.parts) or rel == OUTPUT.relative_to(REPO_ROOT):
            continue
        section = "<root>" if len(rel.parts) == 1 else rel.parts[0]
        target = grouped[section] if section in grouped else grouped["Weitere"]
        target.append(path)
    return grouped


def render(grouped: dict[str, list[Path]]) -> str:
    titles = {"<root>": "Repo-Root", "docs": "Dokumentation", "tag-1": "Tag 1", "tag-2": "Tag 2",
              "tag-3": "Tag 3", "infrastructure": "Infrastructure", "shared": "Shared",
              "scripts": "Scripts", "Weitere": "Weitere"}
    out = [
        "# Inhaltsverzeichnis",
        "",
        "Alle Markdown-Dokumente des Repos. Generiert — bei Änderungen neu erzeugen mit "
        "`python3 scripts/update_inhalt.py`.",
    ]
    for section, files in grouped.items():
        if not files:
            continue
        out += ["", f"## {titles.get(section, section)}", ""]
        for path in files:
            rel = path.relative_to(REPO_ROOT)
            out.append(f"- [{first_heading(path)}](../{rel}) — `{rel}`")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    OUTPUT.write_text(render(collect()), encoding="utf-8")
    total = sum(len(v) for v in collect().values())
    print(f"docs/inhalt.md aktualisiert ({total} Dateien)")
