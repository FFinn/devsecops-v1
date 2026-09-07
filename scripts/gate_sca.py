#!/usr/bin/env python3
"""Контрольная точка SCA для отчёта Trivy с принципом fail-closed."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def strategy_for(vulnerability: dict[str, Any]) -> tuple[str, str]:
    severity = str(vulnerability.get("Severity", "UNKNOWN")).upper()
    fixed = str(vulnerability.get("FixedVersion") or "")

    if severity in {"CRITICAL", "HIGH"} and fixed:
        return "Fix", f"Риск высокий, исправление доступно в версии {fixed}."
    if severity in {"CRITICAL", "HIGH"}:
        return (
            "Monitor",
            "Риск высокий, но исправленная версия не указана. Нужны компенсирующие меры и наблюдение за обновлениями.",
        )
    if severity == "MEDIUM":
        return "Backlog", "Исправление нужно запланировать после проверки контекста использования компонента."
    return "Monitor", "Низкоприоритетный риск зависимости; наблюдать и пересмотреть при появлении новых данных."


def write_triage(path: Path, vulnerabilities: list[dict[str, Any]]) -> None:
    lines = [
        "# Первичный разбор SCA",
        "",
        "Файл сформирован автоматически из фактического отчёта Trivy. Это первичное решение, которое не заменяет проверку специалистом.",
        "",
        "| Компонент | CVE | Уровень | Установлена | Исправлена в | Стратегия | Обоснование |",
        "|---|---|---|---|---|---|---|",
    ]

    if not vulnerabilities:
        lines.append("| - | - | - | - | - | Monitor | В отчёте Trivy известных уязвимостей не найдено. |")
    else:
        for vuln in vulnerabilities[:30]:
            strategy, reason = strategy_for(vuln)
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(vuln.get("PkgName", "-")),
                        str(vuln.get("VulnerabilityID", "-")),
                        str(vuln.get("Severity", "-")),
                        str(vuln.get("InstalledVersion", "-")),
                        str(vuln.get("FixedVersion") or "нет данных"),
                        strategy,
                        reason.replace("|", "\\|"),
                    ]
                )
                + " |"
            )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) not in {3, 4}:
        print(
            "Использование: gate_sca.py <report.json> <gate.log> [triage.md]",
            file=sys.stderr,
        )
        return 2

    report_path = Path(sys.argv[1])
    log_path = Path(sys.argv[2])
    triage_path = Path(sys.argv[3]) if len(sys.argv) == 4 else None

    blocking = {
        item.strip().upper()
        for item in os.getenv("SCA_BLOCK_SEVERITIES", "HIGH,CRITICAL").split(",")
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
        lines.append("причина=обязательный отчёт SCA отсутствует")
        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("\n".join(lines))
        return 2

    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        lines.append("решение=БЛОКИРОВАТЬ")
        lines.append(f"причина=отчёт SCA повреждён или не читается: {exc}")
        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("\n".join(lines))
        return 2

    vulnerabilities: list[dict[str, Any]] = []
    for result in payload.get("Results") or []:
        target = result.get("Target", "неизвестно")
        for vuln in result.get("Vulnerabilities") or []:
            item = dict(vuln)
            item["_target"] = target
            vulnerabilities.append(item)

    if triage_path is not None:
        write_triage(triage_path, vulnerabilities)

    blocked = [
        vuln
        for vuln in vulnerabilities
        if str(vuln.get("Severity", "")).upper() in blocking
    ]

    lines.append(f"всего_уязвимостей={len(vulnerabilities)}")
    lines.append(f"блокирующих_уязвимостей={len(blocked)}")

    for vuln in blocked:
        fixed = vuln.get("FixedVersion") or "нет данных"
        lines.append(
            "блокирующая_уязвимость="
            f"{vuln.get('VulnerabilityID', 'неизвестно')} "
            f"компонент={vuln.get('PkgName', 'неизвестно')} "
            f"установлена={vuln.get('InstalledVersion', 'неизвестно')} "
            f"исправлена={fixed} "
            f"уровень={vuln.get('Severity', 'неизвестно')} "
            f"цель={vuln.get('_target', 'неизвестно')}"
        )

    if blocked:
        lines.append("решение=БЛОКИРОВАТЬ")
        lines.append(
            "следующее_действие=Обновить или заменить компонент либо оформить согласованное "
            "ограниченное по сроку исключение с компенсирующими мерами."
        )
        exit_code = 1
    else:
        lines.append("решение=ПРОПУСТИТЬ")
        lines.append(
            "следующее_действие=Продолжить конвейер; неблокирующие уязвимости при наличии "
            "остаются предметом первичного разбора."
        )
        exit_code = 0

    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
