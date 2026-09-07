# Локальный GitLab 18.1 для финальных скриншотов

Этот compose-файл не участвует в учебном pipeline. Он нужен только для
локального воспроизводимого стенда, на котором можно показать зелёный и
красный GitLab pipeline и снять доказательства для преподавателя.

Используется GitLab CE `18.1.6` — последний найденный patch-релиз ветки 18.1.
Pipeline требует runner с **Docker executor** и тегом `docker`.

## 1. Запуск GitLab

Из корня репозитория:

```bash
docker compose -f local-gitlab/docker-compose.yml up -d
```

Первый старт GitLab может занять несколько минут.

Проверка:

```bash
docker compose -f local-gitlab/docker-compose.yml ps
docker logs -f devsecops-gitlab
```

Откройте:

```text
http://localhost:8080
```

Начальный пароль `root`:

```bash
docker exec devsecops-gitlab \
  grep 'Password:' /etc/gitlab/initial_root_password
```

## 2. Создание проекта

В GitLab создайте пустой проект `devsecops-v1`.

Затем добавьте локальный GitLab как remote и отправьте текущий репозиторий:

```bash
git remote add local-gitlab http://localhost:8080/root/devsecops-v1.git
git push -u local-gitlab main
```

Если проект создаётся не в namespace `root`, замените URL.

## 3. Создание Docker runner

В проекте GitLab:

`Settings → CI/CD → Runners → Create project runner`

Задайте tag:

```text
docker
```

Скопируйте выданный runner authentication token (`glrt-...`).

Затем зарегистрируйте runner:

```bash
docker compose -f local-gitlab/docker-compose.yml exec gitlab-runner \
  gitlab-runner register \
  --non-interactive \
  --url "http://gitlab:8080" \
  --token "<GLRT_TOKEN>" \
  --executor "docker" \
  --docker-image "alpine:3.22"
```

После регистрации откройте:

```text
local-gitlab/runner-config/config.toml
```

В блоке `[[runners]]` добавьте:

```toml
clone_url = "http://host.docker.internal:8080"
```

Для Docker Desktop на macOS это позволяет job-контейнерам клонировать
репозиторий через host port `8080`, потому что URL `localhost:8080` внутри
job-контейнера указывал бы на сам job-контейнер.

Убедитесь, что executor выглядит примерно так:

```toml
executor = "docker"

[runners.docker]
  image = "alpine:3.22"
  volumes = ["/cache"]
```

Перезапустите runner:

```bash
docker compose -f local-gitlab/docker-compose.yml restart gitlab-runner
```

В GitLab runner должен стать `online`.

## 4. Зелёный pipeline

`Build → Pipelines → New pipeline`

Переменная:

```text
SECURITY_DEMO_SCENARIO=green
```

`RUN_DAST=true` уже задано по умолчанию.

Сохраните:

- URL pipeline;
- artifact `publish_security_bundle`;
- скриншот зелёного графа/jobs.

## 5. Красный pipeline

Запустите новый pipeline с:

```text
SECURITY_DEMO_SCENARIO=red-sast
```

Ожидаемо:

- `sast_semgrep` создаёт SAST JSON;
- `sca_trivy` создаёт SCA report + SBOM;
- `gate_sast` завершается ошибкой;
- `gate-sast.log` содержит `decision=BLOCK`;
- последующие deploy/DAST стадии не выполняются.

Сохраните URL и скриншот красного pipeline.

## 6. Финальная фиксация evidence

Из зелёного `publish_security_bundle` скачайте artifact и перенесите его
содержимое в корень репозитория с сохранением путей:

```text
security-reports/
artifacts/ci/
```

Сохраните скриншот как:

```text
artifacts/screenshots/pipeline.png
```

После этого обновите таблицу `Проверка / Mentor` в корневом `README.md` и
сделайте финальный commit.

## Остановка

```bash
docker compose -f local-gitlab/docker-compose.yml down
```

Чтобы удалить также данные GitLab:

```bash
docker compose -f local-gitlab/docker-compose.yml down -v
```
