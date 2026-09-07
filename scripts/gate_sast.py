#!/usr/bin/env python3
"""Контрольная точка SAST с блокировкой по принципу fail-closed."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print("Использование: gate_sast.py <report.json> <gate.log>", file=sys.stderr)
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
        f"время_utc={datetime.now(timezone.utc).isoformat()}",
        f"отчёт={report_path}",
        f"политика=блокировать уровни {','.join(sorted(blocking))}",
    ]

    if not report_path.is_file():
        lines.append("решение=БЛОКИРОВАТЬ")
        lines.append("причина=обязательный отчёт SAST отсутствует")
        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("\n".join(lines))
        return 2

    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        lines.append("решение=БЛОКИРОВАТЬ")
        lines.append(f"причина=отчёт SAST повреждён или не читается: {exc}")
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

    lines.append(f"всего_находок={len(results)}")
    lines.append(f"блокирующих_находок={len(blocked)}")

    for finding in blocked:
        extra = finding.get("extra") or {}
        start = finding.get("start") or {}
        lines.append(
            "блокирующая_находка="
            f"{finding.get('check_id', 'неизвестно')} "
            f"{finding.get('path', 'неизвестно')}:{start.get('line', '?')} "
            f"уровень={extra.get('severity', 'неизвестно')} "
            f"сообщение={extra.get('message', '').replace(chr(10), ' ')}"
        )

    if blocked:
        lines.append("решение=БЛОКИРОВАТЬ")
        lines.append(
            "следующее_действие=Исправить проблему либо оформить согласованное "
            "ограниченное по сроку исключение, затем повторить запуск."
        )
        exit_code = 1
    else:
        lines.append("решение=ПРОПУСТИТЬ")
        lines.append(
            "следующее_действие=Продолжить конвейер; неблокирующие находки при наличии "
            "остаются предметом первичного разбора."
        )
        exit_code = 0

    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
