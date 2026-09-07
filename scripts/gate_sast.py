#!/usr/bin/env python3
"""Fail-closed policy gate for a Semgrep JSON report."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: gate_sast.py <report.json> <gate.log>", file=sys.stderr)
        return 2

    report_path = Path(sys.argv[1])
    log_path = Path(sys.argv[2])
    blocking = {
        item.strip().upper()
        for item in os.getenv("SAST_BLOCK_SEVERITIES", "ERROR").split(",")
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
        lines.append("reason=required SAST report is missing")
        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("\n".join(lines))
        return 2

    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        lines.append("decision=BLOCK")
        lines.append(f"reason=invalid SAST report: {exc}")
        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("\n".join(lines))
        return 2

    results = payload.get("results") or []
    blocked = []
    for finding in results:
        extra = finding.get("extra") or {}
        severity = str(extra.get("severity", "")).upper()
        if severity in blocking:
            blocked.append(finding)

    lines.append(f"findings_total={len(results)}")
    lines.append(f"findings_blocking={len(blocked)}")

    for finding in blocked:
        extra = finding.get("extra") or {}
        start = finding.get("start") or {}
        lines.append(
            "blocked_finding="
            f"{finding.get('check_id', 'unknown')} "
            f"{finding.get('path', 'unknown')}:{start.get('line', '?')} "
            f"severity={extra.get('severity', 'unknown')} "
            f"message={extra.get('message', '').replace(chr(10), ' ')}"
        )

    if blocked:
        lines.append("decision=BLOCK")
        lines.append("next_action=Fix or formally approve a time-bounded exception, then rerun the pipeline.")
        exit_code = 1
    else:
        lines.append("decision=PASS")
        lines.append("next_action=Continue pipeline; non-blocking findings remain subject to triage.")
        exit_code = 0

    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
