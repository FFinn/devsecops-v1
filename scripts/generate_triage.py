#!/usr/bin/env python3
"""Generate a small, preliminary triage summary from SAST/SCA/DAST reports.

This helper is intentionally simple: it does not replace human triage. It
makes the CI artifact easier to review and documents the first decision.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPORTS = Path("security-reports")
OUTPUT = Path("artifacts/ci/triage.md")


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def md(value: Any) -> str:
    return str(value if value not in (None, "") else "-").replace("|", "\\|").replace("\n", " ")


def sast_rows() -> list[list[str]]:
    data = load_json(REPORTS / "sast-report.json")
    rows: list[list[str]] = []
    for item in data.get("results") or []:
        extra = item.get("extra") or {}
        severity = str(extra.get("severity", "UNKNOWN")).upper()
        if severity == "ERROR":
            strategy = "Fix"
            reason = "Blocking SAST finding; fix before merge/release."
        elif severity == "WARNING":
            strategy = "Backlog"
            reason = "Non-blocking SAST finding; confirm context and plan remediation."
        else:
            strategy = "Monitor"
            reason = "Low-priority signal; retain for review."

        start = item.get("start") or {}
        location = f"{item.get('path', '?')}:{start.get('line', '?')}"
        rows.append(
            [
                "SAST",
                md(item.get("check_id")),
                md(severity),
                md(location),
                strategy,
                reason,
            ]
        )
    return rows


def sca_rows() -> list[list[str]]:
    data = load_json(REPORTS / "sca-report.json")
    rows: list[list[str]] = []
    for result in data.get("Results") or []:
        target = result.get("Target", "?")
        for vuln in result.get("Vulnerabilities") or []:
            severity = str(vuln.get("Severity", "UNKNOWN")).upper()
            fixed = vuln.get("FixedVersion") or ""
            if severity in {"CRITICAL", "HIGH"} and fixed:
                strategy = "Fix"
                reason = f"High risk and a fixed version is available: {fixed}."
            elif severity in {"CRITICAL", "HIGH"}:
                strategy = "Monitor"
                reason = "High risk but no fixed version is listed; track vendor update and apply compensating controls."
            elif severity == "MEDIUM":
                strategy = "Backlog"
                reason = "Plan remediation after checking reachability and production context."
            else:
                strategy = "Monitor"
                reason = "Lower-priority dependency risk; monitor and reassess on new data."

            finding = f"{vuln.get('PkgName', '?')} / {vuln.get('VulnerabilityID', '?')}"
            rows.append(
                [
                    "SCA",
                    md(finding),
                    md(severity),
                    md(target),
                    strategy,
                    md(reason),
                ]
            )
    return rows


def dast_rows() -> list[list[str]]:
    data = load_json(REPORTS / "dast-report.json")
    rows: list[list[str]] = []
    for site in data.get("site") or []:
        for alert in site.get("alerts") or []:
            risk_desc = str(alert.get("riskdesc", "UNKNOWN"))
            risk = risk_desc.split(" ", 1)[0].upper()
            name = str(alert.get("name") or alert.get("alert") or "ZAP alert")
            instances = alert.get("instances") or []
            uri = instances[0].get("uri", site.get("@name", "?")) if instances else site.get("@name", "?")

            sensitive_medium = any(
                token in name.lower()
                for token in (
                    "cookie",
                    "content security policy",
                    "x-frame-options",
                    "authentication",
                    "session",
                )
            )
            if risk == "HIGH":
                strategy = "Fix"
                reason = "High-risk DAST signal on a reachable HTTP surface; validate and remediate."
            elif risk == "MEDIUM" and sensitive_medium:
                strategy = "Fix"
                reason = "Medium finding affects browser/session hardening; validate context and remediate."
            elif risk == "MEDIUM":
                strategy = "Backlog"
                reason = "Baseline finding requires contextual triage before becoming a release blocker."
            else:
                strategy = "Monitor"
                reason = "Low/informational baseline signal; keep for hardening and monitoring."

            rows.append(
                [
                    "DAST",
                    md(name),
                    md(risk_desc),
                    md(uri),
                    strategy,
                    reason,
                ]
            )
    return rows


def main() -> int:
    rows = sast_rows() + sca_rows() + dast_rows()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Preliminary security triage",
        "",
        "> Generated automatically from CI reports. This is a first-pass decision and does not replace human review.",
        "",
        "| Source | Finding | Severity/Risk | Location/Target | Strategy | Rationale |",
        "|---|---|---|---|---|---|",
    ]

    if rows:
        for row in rows[:30]:
            lines.append("| " + " | ".join(row) + " |")
    else:
        lines.append("| - | No findings parsed from reports | - | - | Monitor | Recheck scanner output and coverage. |")

    lines.extend(
        [
            "",
            "## Strategy meanings",
            "",
            "- **Fix** — remediate as soon as practical; blocking findings must be resolved before the gate passes.",
            "- **Backlog** — schedule remediation after contextual validation.",
            "- **Accept** — only by a documented, approved and time-bounded exception with compensating controls.",
            "- **Monitor** — track vendor/runtime changes and reassess when new information appears.",
            "",
            "The `Accept` strategy is intentionally not assigned automatically.",
        ]
    )

    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT} with {len(rows)} parsed finding(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
