# Локальный GitLab 18.1 для итоговой проверки

Этот каталог не участвует в работе учебного приложения. Он нужен только для локального стенда, на котором можно запустить GitLab CI/CD, показать успешный и заблокированный прогоны и сделать скриншоты для преподавателя.

Используется GitLab CE `18.1.6`. Ветка 18.1 уже устарела, поэтому стенд предназначен только для локальной учебной работы и не должен быть доступен из интернета.

В `docker-compose.yml` порты GitLab и SSH привязаны к `127.0.0.1`, поэтому сервисы доступны только с локального компьютера.

Для заданий CI/CD нужен GitLab Runner с исполнителем Docker и меткой `docker`.

> В учебной конфигурации GitLab Runner получает доступ к `/var/run/docker.sock`, потому что задание DAST запускает контейнер OWASP ZAP. Такой доступ фактически даёт заданиям CI/CD широкие права на локальный Docker. Используйте эту настройку только на изолированном учебном компьютере и не переносите её в рабочую инфраструктуру без отдельной модели безопасности.

## 1. Запуск GitLab

На macOS сначала добавьте локальное имя в `/etc/hosts`:

```bash
grep -q 'gitlab.local' /etc/hosts || echo '127.0.0.1 gitlab.local' | sudo tee -a /etc/hosts
```

Затем из корня репозитория запустите:

```bash
docker compose -f local-gitlab/docker-compose.yml up -d
```

Первый запуск GitLab может занять несколько минут.

Проверить состояние контейнеров можно так:

```bash
docker compose -f local-gitlab/docker-compose.yml ps
docker logs -f devsecops-gitlab
```

После запуска откройте:

```text
http://gitlab.local:8080
```

Начальный пароль пользователя `root` можно получить командой:

```bash
docker exec devsecops-gitlab \
  grep 'Password:' /etc/gitlab/initial_root_password
```

## 2. Создание проекта

Создайте в GitLab пустой проект `devsecops-v1`.

Добавьте локальный GitLab как дополнительный удалённый репозиторий и отправьте ветку `main`:

```bash
git remote add local-gitlab http://gitlab.local:8080/root/devsecops-v1.git
git push -u local-gitlab main
```

Если проект создан не в пространстве имён `root`, скорректируйте адрес.

## 3. Создание GitLab Runner

В интерфейсе GitLab откройте:

`Settings → CI/CD → Runners → Create project runner`

Задайте метку:

```text
docker
```

Скопируйте выданный токен регистрации вида `glrt-...`.

Затем зарегистрируйте GitLab Runner:

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

На Docker Desktop для macOS это позволяет контейнерам заданий CI/CD клонировать репозиторий через порт хоста `8080`. Адрес `localhost:8080` внутри такого контейнера указывал бы на сам контейнер, а не на GitLab.

Проверьте, что настройка исполнителя выглядит примерно так:

```toml
executor = "docker"

[runners.docker]
  image = "alpine:3.22"
  volumes = ["/cache", "/var/run/docker.sock:/var/run/docker.sock", "/builds:/builds"]
```

Сокет `/var/run/docker.sock` нужен заданию `dast_zap_baseline`: оно запускает официальный контейнер OWASP ZAP. Каталог `/builds` нужен, чтобы контейнер ZAP видел ту же рабочую копию проекта, что и контейнер задания GitLab CI/CD.

Если Docker Desktop на macOS не разрешает подключить `/builds`, укажите рабочий каталог внутри `/Users`. Например:

```toml
builds_dir = "/Users/<user>/PycharmProjects/devsecops-v1/.gitlab-builds"

[runners.docker]
  image = "alpine:3.22"
  volumes = [
    "/cache",
    "/var/run/docker.sock:/var/run/docker.sock",
    "/Users/<user>/PycharmProjects/devsecops-v1/.gitlab-builds:/Users/<user>/PycharmProjects/devsecops-v1/.gitlab-builds"
  ]
```

После изменения конфигурации перезапустите GitLab Runner:

```bash
docker compose -f local-gitlab/docker-compose.yml restart gitlab-runner
```

В интерфейсе GitLab он должен перейти в состояние `online`.

## 4. Успешный прогон

Откройте:

`Build → Pipelines → New pipeline`

Добавьте переменную:

```text
SECURITY_DEMO_SCENARIO=green
```

`RUN_DAST=true` уже задано в `.gitlab-ci.yml`.

После завершения сохраните:

1. адрес прогона;
2. артефакт задания `publish_security_bundle`;
3. скриншот успешного графа заданий CI/CD.

## 5. Заблокированный прогон SAST

Запустите новый прогон с переменной:

```text
SECURITY_DEMO_SCENARIO=red-sast
```

Ожидаемый результат:

1. `sast_semgrep` создаёт отчёт SAST в JSON;
2. `sca_trivy` создаёт отчёт SCA и SBOM;
3. `gate_sast` находит блокирующие записи уровня `ERROR` и завершается ошибкой;
4. в `gate-sast.log` появляется `решение=БЛОКИРОВАТЬ`;
5. этапы проверки цели DAST и динамического сканирования не выполняются.

Сохраните адрес прогона и скриншот.

## 6. Заблокированный прогон SCA

Чтобы получить фактические находки Trivy для первичного разбора SCA, запустите:

```text
SECURITY_DEMO_SCENARIO=red-sca
```

Ожидаемый результат:

1. Trivy анализирует учебный файл с устаревшими зависимостями;
2. сохраняется настоящий `sca-report.json`;
3. `gate_sca` формирует `gate-sca.log` и `triage-sca.md`;
4. при наличии `HIGH` или `CRITICAL` дальнейшее выполнение блокируется.

Скачайте артефакты `sca_trivy` и `gate_sca`. Они нужны для подтверждения SCA-разбора в итоговой работе.

## 7. Сохранение материалов для проверки

После новых прогонов перенесите содержимое артефактов в репозиторий с сохранением путей:

```text
security-reports/
artifacts/ci/
```

Скриншоты сохраните отдельно:

```text
artifacts/screenshots/pipeline-green.png
artifacts/screenshots/pipeline-red.png
```

После этого обновите раздел «Материалы для проверки» в корневом `README.md` и сделайте итоговый коммит.

## 8. Остановка локального стенда

Остановить контейнеры:

```bash
docker compose -f local-gitlab/docker-compose.yml down
```

Удалить контейнеры вместе с данными GitLab:

```bash
docker compose -f local-gitlab/docker-compose.yml down -v
```
