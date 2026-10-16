# Практическая работа № 4

## Jenkins Pipeline и Docker

### Задание

Реализовать Jenkins Pipeline, который выполняет следующие действия:

1. Получает исходный код веб-приложения из практической работы № 2 из репозитория GitHub.
2. Собирает Docker-образ приложения.
3. Разворачивает приложение, запуская Docker-контейнер.

### Требования

`Dockerfile` должен изначально находиться в репозитории GitHub вместе с исходным кодом приложения.

Pipeline должен запускаться на Jenkins и содержать понятные этапы получения кода, сборки образа и запуска контейнера.

### Результат

После успешного выполнения Pipeline работающее приложение должно быть доступно для проверки в запущенном контейнере.

### Запуск и проверка на macOS и Windows

Jenkins Pipeline выполняется на Linux-агенте с меткой `docker-linux`: это
важно, поскольку в `Jenkinsfile` используются команды `sh`. Mac или Windows
могут быть хостом Docker Desktop и Jenkins-контроллера, но не Windows-агентом
для этого Pipeline.

1. Установите Docker Desktop и включите режим Linux containers.
2. Создайте Jenkins Pipeline job: `Pipeline script from SCM`, ветка `*/master`,
   Script Path `Jenkinsfile`, затем нажмите **Build Now**.
3. В Console Output должны успешно завершиться стадии: получение исходников,
   сборка образа, запуск контейнера и проверка приложения.
4. На Jenkins-агенте проверьте `http://127.0.0.1:8081/health`: ожидаемый
   ответ — `{"status":"ok"}`. Для удалённого агента используйте SSH-туннель.

До настройки Jenkins можно воспроизводимо проверить Docker-часть из корня
репозитория. На macOS/Linux:

```bash
docker build -t repair-tracker:practice-check .
REPAIR_IMAGE=repair-tracker:practice-check APP_PORT=8081 \
  docker compose --project-name repair-tracker-practice-check -f ci/compose.yaml up -d --wait
curl http://127.0.0.1:8081/health
REPAIR_IMAGE=repair-tracker:practice-check APP_PORT=8081 \
  docker compose --project-name repair-tracker-practice-check -f ci/compose.yaml down
```

В Windows PowerShell используйте те же команды в следующем виде:

```powershell
docker build -t repair-tracker:practice-check .
$env:REPAIR_IMAGE = 'repair-tracker:practice-check'
$env:APP_PORT = '8081'
docker compose --project-name repair-tracker-practice-check -f ci/compose.yaml up -d --wait
Invoke-RestMethod http://127.0.0.1:8081/health
docker compose --project-name repair-tracker-practice-check -f ci/compose.yaml down
```

Команда `down` не содержит `-v`, поэтому не удаляет том с данными.
