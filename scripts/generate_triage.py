#!/usr/bin/env python3
"""Формирует краткий первичный разбор по отчётам SAST, SCA и DAST.

Сводка помогает быстро посмотреть результаты одного прогона, но не заменяет
ручную проверку находок специалистом.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPORTS = Path("security-reports")
OUTPUT = Path("artifacts/ci/triage.md")

DAST_NAMES_RU = {
    "Content Security Policy (CSP) Header Not Set": "Не задан заголовок Content-Security-Policy (CSP)",
    "Cross-Domain Misconfiguration": "Ошибочная междоменная конфигурация",
    "Cross-Origin-Embedder-Policy Header Missing or Invalid": "Заголовок Cross-Origin-Embedder-Policy отсутствует или задан неверно",
    "Cross-Origin-Opener-Policy Header Missing or Invalid": "Заголовок Cross-Origin-Opener-Policy отсутствует или задан неверно",
    "Dangerous JS Functions": "Используются потенциально опасные функции JavaScript",
    "Deprecated Feature Policy Header Set": "Используется устаревший заголовок Feature-Policy",
    "Permissions Policy Header Not Set": "Не задан заголовок Permissions-Policy",
    'Server Leaks Version Information via "Server" HTTP Response Header Field': "Сервер раскрывает версию через HTTP-заголовок Server",
    "Strict-Transport-Security Header Not Set": "Не задан заголовок Strict-Transport-Security",
    "Timestamp Disclosure - Unix": "Раскрывается временная метка Unix",
    "Modern Web Application": "Обнаружено современное веб-приложение",
    "Re-examine Cache-control Directives": "Нужно проверить директивы Cache-Control",
    "Storable and Cacheable Content": "Содержимое можно сохранять и кэшировать",
    "Storable but Non-Cacheable Content": "Содержимое можно сохранять, но оно не кэшируется",
    "Cookie No HttpOnly Flag": "У cookie не установлен флаг HttpOnly",
    "Cookie Secure Flag Not Set": "У cookie не установлен флаг Secure",
    "X-Frame-Options Header Not Set": "Не задан заголовок X-Frame-Options",
}


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
            reason = "Блокирующая SAST-находка: исправить до слияния или выпуска."
        elif severity == "WARNING":
            strategy = "Backlog"
            reason = "Находка не блокирует выпуск: проверить контекст и запланировать исправление."
        else:
            strategy = "Monitor"
            reason = "Низкоприоритетный сигнал: сохранить для повторной проверки."

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
                reason = f"Риск высокий, исправленная версия доступна: {fixed}."
            elif severity in {"CRITICAL", "HIGH"}:
                strategy = "Monitor"
                reason = "Риск высокий, но исправленная версия не указана: нужны компенсирующие меры и наблюдение за обновлениями."
            elif severity == "MEDIUM":
                strategy = "Backlog"
                reason = "Запланировать исправление после проверки достижимости и контекста использования в рабочем контуре."
            else:
                strategy = "Monitor"
                reason = "Низкоприоритетный риск зависимости: наблюдать и пересмотреть при появлении новых данных."

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
            original_name = str(alert.get("name") or alert.get("alert") or "")
            plugin_id = str(alert.get("pluginid") or alert.get("alertRef") or "?")
            name = DAST_NAMES_RU.get(original_name, f"Срабатывание правила OWASP ZAP №{plugin_id}")
            instances = alert.get("instances") or []
            uri = instances[0].get("uri", site.get("@name", "?")) if instances else site.get("@name", "?")

            sensitive_medium = any(
                token in original_name.lower()
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
                reason = "Сигнал высокого риска на доступной HTTP-поверхности: проверить контекст и исправить."
            elif risk == "MEDIUM" and sensitive_medium:
                strategy = "Fix"
                reason = "Находка среднего риска влияет на защиту браузера или сессии: проверить и исправить."
            elif risk == "MEDIUM":
                strategy = "Backlog"
                reason = "Находка базового DAST-сканирования требует проверки контекста перед возможной блокировкой выпуска."
            else:
                strategy = "Monitor"
                reason = "Низкоприоритетный или информационный сигнал: оставить в плане усиления защиты и наблюдать."

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
        "# Первичный разбор результатов безопасности",
        "",
        "> Сводка сформирована автоматически из отчётов текущего прогона. Это первое решение, а не замена ручной проверки специалистом.",
        "",
        "| Источник | Находка | Уровень / риск | Файл, компонент или адрес | Стратегия | Обоснование |",
        "|---|---|---|---|---|---|",
    ]

    if rows:
        for row in rows[:30]:
            lines.append("| " + " | ".join(row) + " |")
    else:
        lines.append("| - | Разобранных находок нет | - | - | Monitor | Проверить отчёты сканеров и охват анализа. |")

    lines.extend(
        [
            "",
            "## Значение стратегий",
            "",
            "- **Fix** — исправить; блокирующие проблемы должны быть устранены до прохождения контрольной точки.",
            "- **Backlog** — запланировать исправление после проверки контекста.",
            "- **Accept** — принять риск только через документированное, согласованное и ограниченное по сроку исключение с компенсирующими мерами.",
            "- **Monitor** — наблюдать за изменениями и повторно оценивать риск при появлении новых данных.",
            "",
            "Стратегия `Accept` намеренно не назначается автоматически.",
        ]
    )

    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Создан {OUTPUT}; разобрано находок: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
