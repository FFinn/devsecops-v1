# DevSecOps Security Pipeline: SAST + SCA + DAST

Финальная практическая работа по спринту DevSecOps. Репозиторий демонстрирует единый
GitLab CI/CD security pipeline, в котором результаты сканеров превращаются в
воспроизводимые отчёты, SBOM и решения security gates.

## Проверка / Mentor

После финального локального прогона заполните две ссылки и добавьте реальный
скриншот pipeline. Остальные пути уже фиксированы пайплайном.

| Что | Где |
|---|---|
| Зелёный pipeline | `<добавить ссылку после локального запуска GitLab>` |
| Красный pipeline | `<добавить ссылку после локального запуска GitLab>` |
| DAST target | `https://preview.owasp-juice.shop/` |
| SAST отчёт | `security-reports/sast-report.json` |
| SCA отчёт | `security-reports/sca-report.json` |
| SBOM | `security-reports/sbom.json` |
| DAST HTML | `security-reports/dast-report.html` |
| DAST JSON | `security-reports/dast-report.json` |
| SAST gate log | `artifacts/ci/gate-sast.log` |
| SCA gate log | `artifacts/ci/gate-sca.log` |
| DAST policy log | `artifacts/ci/gate-dast.log` |
| ZAP log | `artifacts/ci/zap-baseline-log.txt` |
| Автоматический triage | `artifacts/ci/triage.md` |
| Скриншот | `artifacts/screenshots/pipeline.png` |

> Отчёты и логи генерируются CI и сохраняются как GitLab job artifacts.
> После финальных прогонов их можно скачать из `publish_security_bundle`,
> распаковать в эти же каталоги и закоммитить вместе со скриншотом, если
> преподаватель требует физическое наличие результатов в Git-репозитории.

## 1. Структура проекта

```text
.
├── .gitlab-ci.yml
├── app/
│   └── database.py
├── requirements.txt
├── security/
│   └── semgrep.yml
├── security-fixtures/
│   ├── red-sast/
│   │   └── database.py
│   └── red-sca/
│       └── requirements.txt.fixture
├── scripts/
│   ├── gate_sast.py
│   ├── gate_sca.py
│   └── generate_triage.py
├── security-reports/
└── artifacts/
    ├── ci/
    └── screenshots/
```

`app/database.py` содержит безопасный вариант запросов с параметризацией.
Уязвимые примеры вынесены в `security-fixtures/` и сканируются только при
явном запуске демонстрационного красного сценария.

## 2. Стадии pipeline

| Стадия | Job | Назначение |
|---|---|---|
| `verify` | `sast_semgrep` | Semgrep сканирует Python-код и сохраняет JSON |
| `build` | `sca_trivy` | Trivy сканирует зависимости и формирует CycloneDX SBOM |
| `gate` | `gate_sast` | Блокирует по SAST severity `ERROR` |
| `gate` | `gate_sca` | Блокирует по SCA severity `HIGH` / `CRITICAL` |
| `deploy_test` | `deploy_test` | Проверяет доступность внешнего test/stage DAST target |
| `security` | `dast_zap_baseline` | OWASP ZAP baseline проверяет работающую цель |
| `publish` | `publish_security_bundle` | Проверяет наличие результатов, формирует triage и итоговый bundle |

SAST и SCA выполняются до DAST. DAST запускается только тогда, когда есть
подходящий test/stage контур: на default branch, `release/*` или при ручном
web-запуске. На обычном Merge Request DAST не запускается.

## 3. SAST — Semgrep

Используется Semgrep Community Edition и локальный набор правил
`security/semgrep.yml`. Локальные правила делают учебный результат
воспроизводимым и не зависят от изменения удалённого registry ruleset.

Правила ищут два варианта потенциальной SQL Injection:

- SQL собирается через конкатенацию;
- SQL собирается через `f-string`.

В зелёном сценарии сканируется `app/`, где запросы параметризованы.
В `red-sast` сканируется `security-fixtures/red-sast/`, содержащий два
намеренно уязвимых примера.

Результат:

```text
security-reports/sast-report.json
```

Semgrep job сам по себе формирует сигнал. Решение о блокировке принимает
отдельный `gate_sast`.

## 4. SCA — Trivy и SBOM

Trivy анализирует зависимости проекта и сохраняет:

```text
security-reports/sca-report.json
security-reports/sbom.json
```

`sbom.json` формируется в формате CycloneDX.

Для обычного зелёного сценария используются зависимости из
`requirements.txt`. Для отдельной демонстрации SCA-gate можно запустить
`SECURITY_DEMO_SCENARIO=red-sca`: тогда fixture с заведомо устаревшими
зависимостями копируется во временный `requirements.txt` и анализируется
Trivy. Исходный fixture специально имеет суффикс `.fixture`, поэтому
обычное сканирование проекта не воспринимает его как рабочий manifest.

## 5. DAST — OWASP ZAP baseline

Цель задаётся переменной:

```text
DAST_TARGET=https://preview.owasp-juice.shop/
```

Перед ZAP job `deploy_test` проверяет, что внешний учебный test/stage target
доступен по HTTP(S). Затем `dast_zap_baseline` запускает baseline scan и
сохраняет два представления отчёта:

```text
security-reports/dast-report.html
security-reports/dast-report.json
```

Также сохраняется полный вывод ZAP:

```text
artifacts/ci/zap-baseline-log.txt
```

Baseline запускается с `-I`: обычные `WARN` не делают pipeline красным и
поступают в triage. Это осознанная политика: baseline DAST сильно зависит от
окружения и coverage, поэтому любая предупреждающая находка не становится
автоматическим stop-фактором.

При этом DAST ведёт себя fail-closed при технической ошибке сканера,
отсутствии обязательного HTML-отчёта или если правило ZAP явно настроено как
`FAIL`.

## 6. Security gates

Сканеры и gates разделены намеренно: сканер формирует отчёт, gate читает
результат и применяет политику.

| Проверка | Где применяется | Условие блокировки | Обоснование |
|---|---|---|---|
| SAST | `gate` до deploy | Есть finding severity `ERROR` | Ошибку в собственном коде нужно остановить до доставки |
| SCA | `gate` до deploy | Есть `HIGH` или `CRITICAL` | Такой риск в зависимости слишком высок для автоматического продвижения |
| DAST baseline | `security` / stage | `WARN` → triage; `FAIL`, ошибка сканера или нет отчёта → block | DAST требует контекста и стабильного окружения |

Gates работают по fail-closed для обязательных отчётов: если JSON отсутствует
или повреждён, `gate_sast.py` / `gate_sca.py` завершаются ошибкой.

После срабатывания gate команда должна:

1. открыть отчёт и gate log;
2. подтвердить контекст;
3. выбрать `Fix`, `Backlog`, `Accept` или `Monitor`;
4. для блокирующей проблемы выполнить `Fix` либо оформить согласованное,
   ограниченное по сроку исключение с компенсирующими мерами;
5. повторно запустить pipeline.

Порог можно изменить через `SAST_BLOCK_SEVERITIES` и
`SCA_BLOCK_SEVERITIES`, но изменение policy должно быть отдельно
задокументировано.

## 7. Triage

`publish_security_bundle` запускает `scripts/generate_triage.py` и создаёт
предварительную сводку:

```text
artifacts/ci/triage.md
```

Это первый автоматизированный triage, а не окончательное решение специалиста.

Базовая логика:

- SAST `ERROR` → `Fix`;
- SCA `HIGH`/`CRITICAL` с `FixedVersion` → `Fix`;
- SCA `HIGH`/`CRITICAL` без исправления → `Monitor` + компенсирующие меры до
  появления исправления; `Accept` возможен только как формальное исключение;
- SCA `MEDIUM` → `Backlog`;
- DAST `HIGH` → `Fix`;
- DAST `MEDIUM` по session/cookie/CSP/X-Frame-Options → `Fix` после проверки
  контекста;
- остальные `MEDIUM` baseline → `Backlog`;
- `LOW`/informational → `Monitor`.

`Accept` намеренно не назначается автоматически.

Контролируемые SAST-находки красного сценария:

| Finding | Strategy | Почему |
|---|---|---|
| SQL query через конкатенацию | `Fix` | Потенциальная CWE-89, severity `ERROR`; заменить на параметризованный запрос |
| SQL query через `f-string` | `Fix` | Пользовательский ввод попадает в SQL; использовать параметры DB API |

Фактические CVE Trivy и DAST alerts зависят от актуальных баз и состояния
внешней цели; финальный `triage.md` формируется именно из отчётов конкретного
pipeline.

## 8. Зелёный сценарий

Запустите pipeline с переменной:

```text
SECURITY_DEMO_SCENARIO=green
```

Это значение установлено по умолчанию.

Ожидаемая последовательность:

```text
sast_semgrep
  ↓
sca_trivy
  ↓
gate_sast + gate_sca
  ↓
deploy_test
  ↓
dast_zap_baseline
  ↓
publish_security_bundle
```

Pipeline зелёный, если SAST/SCA gates не нашли блокирующих результатов,
внешняя цель доступна, ZAP завершился штатно и обязательные артефакты
сформированы. Наличие неблокирующих DAST WARN допустимо и отражается в
triage.

## 9. Красный сценарий

Для воспроизводимого красного прогона в **Run pipeline** задайте:

```text
SECURITY_DEMO_SCENARIO=red-sast
```

`sast_semgrep` просканирует намеренно уязвимый fixture и сохранит JSON.
`gate_sast` найдёт `ERROR` и завершится с кодом `1`.

В `artifacts/ci/gate-sast.log` будет видно:

```text
policy=block severities ERROR
findings_blocking=...
decision=BLOCK
```

Это не искусственный `exit 1`: pipeline падает именно по содержимому
Semgrep-отчёта.

Дополнительный красный сценарий для SCA:

```text
SECURITY_DEMO_SCENARIO=red-sca
```

Его результат зависит от актуальной Trivy vulnerability database, но
намеренно старые версии выбраны так, чтобы продемонстрировать SCA findings.

## 10. Артефакты

Каждый security job использует `artifacts: when: always`, поэтому report или
gate log сохраняется даже при падении соответствующего gate.

В полном зелёном прогоне `publish_security_bundle` собирает единый artifact:

```text
security-reports/
artifacts/ci/
```

Срок хранения CI artifacts в учебной конфигурации — `30 days`.

## 11. Что осталось сделать перед сдачей

После переноса проекта в локальный GitLab:

1. зарегистрировать Docker executor runner с тегом `docker`;
2. выполнить зелёный pipeline;
3. выполнить `red-sast` pipeline;
4. скачать artifacts обоих прогонов;
5. добавить реальные ссылки на pipelines в таблицу **Проверка / Mentor**;
6. сделать скриншот графа/списка jobs и сохранить как
   `artifacts/screenshots/pipeline.png`;
7. при требовании преподавателя к физическим файлам в Git — распаковать
   artifact `publish_security_bundle` в корень репозитория и закоммитить
   реальные `security-reports/` и `artifacts/ci/`.

## Используемые инструменты

- Semgrep Community Edition — `semgrep/semgrep:1.172.0`
- Trivy — `aquasec/trivy:0.74.0`
- OWASP ZAP — `ghcr.io/zaproxy/zaproxy:stable`
- GitLab CI/CD с Docker executor runner
