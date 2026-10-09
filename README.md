# Трекер заявок на ремонт техники

Практическая работа № 2: веб-приложение с формой ввода, списком заявок,
просмотром, редактированием и удалением. Данные хранятся в SQLite.

## Запуск

Нужен Python 3.10 или новее.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Открыть http://127.0.0.1:5050. База создаётся в `data/requests.db` и не входит
в Git. Приложение предназначено для локальной демонстрации.

## Работа в ветках

- `master`: общая основа, единая структура данных и итоговые слияния.
- `feature/request-form`: morning728, форма создания заявки.
- `feature/request-list`: Hotway97, список и управление заявками.

Обе рабочие ветки начинаются от одного исходного коммита. Сообщения коммитов
написаны на русском. Имена и email авторов соответствуют двум аккаунтам.

## Запуск в Docker

Нужен работающий Docker с поддержкой Linux-контейнеров и Docker Compose.

```bash
git clone https://github.com/morning728/repair-tracker.git
cd repair-tracker
docker compose up -d --build
```

Открыть http://localhost:8080. При сборке автоматически запускаются тесты.
Контейнер работает от непривилегированного пользователя, HTTP обслуживает
Gunicorn. Проверка `/health` подтверждает доступность приложения и базы.
Первоначально каталог пуст: добавьте заявку через форму.

```bash
docker compose ps
docker compose logs --tail=50
docker compose down
```

База сохраняется в именованном томе `repair-data` и переживает обычный
`docker compose down` и повторный запуск. Команда `down -v` удаляет том вместе
с данными, поэтому для обычной остановки её использовать не нужно.

Если порт 8080 занят, в PowerShell задайте другой перед запуском:

```powershell
$env:APP_PORT = '8081'
docker compose up -d --build
```

В таком случае адрес будет http://localhost:8081. Порт публикуется только
на локальном интерфейсе; приложение не содержит авторизации пользователей.
Один и тот же проект запускается на Windows, Linux и macOS с Docker.

## Тесты и история

```bash
python -m unittest discover -s tests -v
git log --graph --oneline --decorate --all
```

Подробное распределение работы и пояснения для защиты: `DEVELOPMENT.md`.

## Практическая работа № 3: Ansible

Цель работы — доставить приложение из практической работы № 2 на Ubuntu-сервер
и запустить его с помощью Ansible. Плейбук `ansible/deploy.yml` автоматически:

1. проверяет Ubuntu 22.04/24.04 и архитектуру `amd64`/`arm64`;
2. устанавливает Docker Engine, Buildx и Compose Plugin;
3. запускает Docker и добавляет его в автозагрузку;
4. создаёт каталог `/opt/repair-tracker`;
5. копирует исходный код, шаблоны, статику, `Dockerfile` и тесты на сервер;
6. формирует Compose-файл и собирает Docker-образ;
7. запускает контейнер и проверяет endpoint `/health`.

### Подготовка управляющей машины

Ansible запускается с Linux-машины, WSL или отдельной Ubuntu VM. На ней
должны быть Python 3.12+, SSH-клиент и Git:

```bash
sudo apt update
sudo apt install -y python3 python3-venv git openssh-client
git clone https://github.com/morning728/repair-tracker.git
cd repair-tracker
python3 -m venv .ansible-venv
source .ansible-venv/bin/activate
python -m pip install -r ansible/requirements-control.txt
ansible-galaxy collection install -r ansible/requirements.yml
cd ansible
cp inventory.ini.example inventory.ini
```

### Настройка сервера

В `ansible/inventory.ini` замените пример IP, пользователя и путь к SSH-ключу:

```ini
[repair_servers]
repair-server ansible_host=SERVER_IP ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/repair_server
```

Целевой сервер должен иметь Ubuntu 22.04/24.04, Python 3, SSH-доступ и права
`sudo`. Перед запуском плейбука проверьте подключение:

```bash
ssh -i ~/.ssh/repair_server ubuntu@SERVER_IP
sudo -v
exit
```

Проверка и развёртывание выполняются из каталога `ansible`:

```bash
ansible repair_servers -m ansible.builtin.ping
ansible-playbook deploy.yml --syntax-check
ansible-playbook deploy.yml --ask-become-pass
```

Если `sudo` не требует пароль, последний параметр можно убрать. Исходники
передаются с управляющей машины, поэтому GitHub-ключ на сервер не копируется.

### Проверка приложения

По умолчанию приложение публикуется только на `127.0.0.1:8080` сервера.
Для доступа с локального компьютера используйте SSH-туннель:

```bash
ssh -N -L 8080:127.0.0.1:8080 -i ~/.ssh/repair_server ubuntu@SERVER_IP
```

После этого откройте <http://localhost:8080>. На сервере состояние можно
проверить командами:

```bash
sudo docker compose -f /opt/repair-tracker/compose.yaml ps
curl http://127.0.0.1:8080/health
```

SQLite хранится в Docker volume и сохраняется при повторном запуске плейбука.
Подробная инструкция находится в [ansible/README.md](ansible/README.md),
формулировка задания — в [practice/practice-3.md](practice/practice-3.md).

## Практическая работа № 4: Jenkins Pipeline и Docker

Цель работы — настроить Jenkins Pipeline, который получает исходный код из
GitHub, собирает Docker-образ и запускает контейнер на Jenkins-агенте.

Pipeline находится в файле `Jenkinsfile`. Его этапы:

1. получение исходников из GitHub;
2. проверка Docker, Compose, Python и параметра порта;
3. сборка Docker-образа командой `docker build`;
4. запуск контейнера через `ci/compose.yaml`;
5. проверка `http://127.0.0.1:<APP_PORT>/health`.

Сборка Docker-образа также запускает тесты из каталога `tests`, поскольку
команда тестирования включена в `Dockerfile`. Образ получает тег вида
`repair-tracker:build-<номер>-<git-sha>`.

### Требования к Jenkins-агенту

Агент должен работать под Linux и иметь:

- Git;
- Python 3.12 или новее и `venv`;
- Docker и Docker Compose v2.18 или новее;
- доступ к Docker Engine;
- доступ к GitHub, Docker Hub и PyPI.

Агент должен иметь метку `docker-linux`, потому что она указана в
`Jenkinsfile`. Обычный Windows-агент для этого Pipeline не подходит: в нём
используются Linux-команды `sh`.

### Создание Jenkins-задачи

1. Создайте Pipeline job, например `repair-tracker-local`.
2. Выберите `Pipeline script from SCM`.
3. Укажите Git-репозиторий проекта и ветку `*/master`.
4. Укажите путь к Pipeline: `Jenkinsfile`.
5. Запустите `Build Now` или сборку с параметрами.

Параметр `APP_PORT` по умолчанию равен `8081`. После успешной сборки приложение
будет доступно на Jenkins-агенте по адресу `http://127.0.0.1:8081`. Внутри
контейнера приложение работает на порту `8000`.

Pipeline не допускает параллельные сборки одной задачи и сохраняет последние
10 сборок. Подробные требования к Jenkins описаны в [ci/README.md](ci/README.md),
формулировка задания — в [practice/practice-4.md](practice/practice-4.md).

## Практическая работа № 5: Jenkins + Ansible

Цель работы — дополнить Pipeline из практической работы № 4 доставкой готового
Docker-образа на Ubuntu-сервер и его развёртыванием через Ansible.

В `Jenkinsfile.ansible` Pipeline выполняет следующие этапы:

1. получает исходники и Ansible-плейбук из GitHub;
2. создаёт отдельное Ansible-окружение и устанавливает зависимости;
3. проверяет параметры сервера и формирует временный inventory;
4. собирает Docker-образ и запускает встроенные тесты;
5. сохраняет образ в `tmp/repair-image.tar`;
6. сохраняет SHA256 и метаданные образа как артефакты Jenkins;
7. передаёт архив на сервер через Ansible;
8. загружает образ в Docker без Docker Registry и запускает приложение;
9. проверяет совместимость архитектуры и endpoint `/health`.

Для этой практики используется `ansible/deploy_image.yml`. В отличие от
`deploy.yml`, он не копирует исходники и не собирает приложение на сервере:
сервер получает уже проверенный Docker-образ из Jenkins.

### Credentials Jenkins

Создайте следующие credentials:

| ID | Тип | Назначение |
| --- | --- | --- |
| `repair-server-ssh` | SSH Username with private key | SSH-доступ к Ubuntu-серверу |
| `repair-server-known-hosts` | Secret file | Проверенный публичный ключ SSH-сервера |
| `repair-server-sudo` | Secret text, необязательно | Пароль `sudo`, если он требуется |

Приватный ключ и пароль нельзя хранить в репозитории или в inventory.
Проверка SSH выполняется с включённым `StrictHostKeyChecking`.

### Создание Jenkins-задачи

Создайте вторую Pipeline job, например `repair-tracker-server`, с тем же
репозиторием и веткой, но укажите путь `Jenkinsfile.ansible`.

При запуске задайте параметры:

| Параметр | Пример |
| --- | --- |
| `SERVER_HOST` | IP или DNS-имя Ubuntu-сервера |
| `SERVER_USER` | `ubuntu` |
| `SERVER_SSH_PORT` | `22` |
| `SERVER_APP_PORT` | `8080` |
| `SERVER_SSH_CREDENTIAL_ID` | `repair-server-ssh` |
| `SERVER_KNOWN_HOSTS_ID` | `repair-server-known-hosts` |
| `SERVER_SUDO_CREDENTIAL_ID` | пусто или `repair-server-sudo` |

Сервер должен иметь Ubuntu 22.04/24.04, Docker, Compose и архитектуру,
совместимую с Jenkins-агентом. Pipeline проверяет ОС и архитектуру перед
запуском приложения. После успешного деплоя проверка выполняется на сервере
по `http://127.0.0.1:8080/health`; для просмотра с локального компьютера
используйте SSH-туннель:

```bash
ssh -N -L 8082:127.0.0.1:8080 ubuntu@SERVER_IP
```

После этого приложение открывается по адресу <http://localhost:8082>.
Подробная инструкция находится в [ci/README.md](ci/README.md) и
[ansible/README.md](ansible/README.md), формулировка задания — в
[practice/practice-5.md](practice/practice-5.md).
