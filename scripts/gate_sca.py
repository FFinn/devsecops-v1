#!/usr/bin/env python3
"""Fail-closed policy gate for a Trivy filesystem JSON report."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: gate_sca.py <report.json> <gate.log>", file=sys.stderr)
        return 2

    report_path = Path(sys.argv[1])
    log_path = Path(sys.argv[2])
    blocking = {
        item.strip().upper()
        for item in os.getenv("SCA_BLOCK_SEVERITIES", "HIGH,CRITICAL").split(",")
        if item.strip()
    }

    log_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"timestamp_utc={datetime.now(timezone.utc).isoformat()}",
        f"report={report_path}",
        f"policy=block severities {','.join(sorted(blocking))}",
    ]

    if not report_path.is_file():
        lines.append("decision=BLOCK")
        lines.append("reason=required SCA report is missing")
        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("\n".join(lines))
        return 2

    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        lines.append("decision=BLOCK")
        lines.append(f"reason=invalid SCA report: {exc}")
        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("\n".join(lines))
        return 2

    vulnerabilities = []
    for result in payload.get("Results") or []:
        target = result.get("Target", "unknown")
        for vuln in result.get("Vulnerabilities") or []:
            item = dict(vuln)
            item["_target"] = target
            vulnerabilities.append(item)

    blocked = [
        vuln
        for vuln in vulnerabilities
        if str(vuln.get("Severity", "")).upper() in blocking
    ]

    lines.append(f"vulnerabilities_total={len(vulnerabilities)}")
    lines.append(f"vulnerabilities_blocking={len(blocked)}")

    for vuln in blocked:
        fixed = vuln.get("FixedVersion") or "none"
        lines.append(
            "blocked_vulnerability="
            f"{vuln.get('VulnerabilityID', 'unknown')} "
            f"package={vuln.get('PkgName', 'unknown')} "
            f"installed={vuln.get('InstalledVersion', 'unknown')} "
            f"fixed={fixed} "
            f"severity={vuln.get('Severity', 'unknown')} "
            f"target={vuln.get('_target', 'unknown')}"
        )

    if blocked:
        lines.append("decision=BLOCK")
        lines.append("next_action=Upgrade/remediate, or document an approved time-bounded exception with compensating controls.")
        exit_code = 1
    else:
        lines.append("decision=PASS")
        lines.append("next_action=Continue pipeline; lower-severity findings remain subject to triage.")
        exit_code = 0

    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
