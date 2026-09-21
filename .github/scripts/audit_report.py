"""Render a pip-audit JSON report as a GitHub Actions step summary.

Reads the JSON produced by `pip-audit --format=json` and writes a Markdown table to
`$GITHUB_STEP_SUMMARY` (or stdout when running locally). Exits non-zero when at least one
vulnerability has a fix available, so the pipeline fails on something that is actionable
and only warns about advisories nobody can do anything about yet.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

MAX_ALIASES = 3


def _rows(report: dict) -> list[dict]:
    """Flatten the report into one row per advisory.

    pip-audit can list the same advisory more than once for a package, so rows are keyed
    on (package, version, advisory id) and the duplicates are dropped.
    """
    rows: dict[tuple[str, str, str], dict] = {}
    for dep in report.get("dependencies", []):
        name = dep.get("name", "?")
        version = dep.get("version", "?")
        for vuln in dep.get("vulns", []):
            key = (name, version, vuln.get("id", "?"))
            rows.setdefault(
                key,
                {
                    "name": name,
                    "version": version,
                    "id": key[2],
                    "aliases": sorted(vuln.get("aliases") or []),
                    "fix": ", ".join(vuln.get("fix_versions") or []),
                },
            )
    return list(rows.values())


def _render(rows: list[dict], total: int) -> str:
    if not rows:
        return f"## Dependency audit\n\nNo known vulnerabilities in **{total}** resolved packages.\n"

    fixable = [r for r in rows if r["fix"]]
    lines = [
        "## Dependency audit",
        "",
        (f"**{len(rows)}** advisories across **{total}** resolved packages ({len(fixable)} with a fix available)."),
        "",
        "| Package | Installed | Advisory | Also known as | Fixed in |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in sorted(rows, key=lambda r: (not r["fix"], r["name"])):
        aliases = ", ".join(row["aliases"][:MAX_ALIASES]) or "—"
        fix = f"**{row['fix']}**" if row["fix"] else "_no fix yet_"
        lines.append(f"| `{row['name']}` | {row['version']} | {row['id']} | {aliases} | {fix} |")
    lines.append("")
    if fixable:
        lines.append("Upgrade the packages marked **Fixed in** and re-run `pdm lock`.")
    else:
        lines.append("Every advisory is still unfixed upstream. Nothing to do right now.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    """Write the report and return the exit code for the workflow step."""
    report_path = Path(sys.argv[1] if len(sys.argv) > 1 else "audit.json")
    report = json.loads(report_path.read_text())
    rows = _rows(report)
    total = len(report.get("dependencies", []))

    summary = _render(rows, total)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as handle:
            handle.write(summary)
    print(summary)

    return 1 if any(row["fix"] for row in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
