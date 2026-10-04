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

Плейбук `ansible/deploy.yml` устанавливает Docker на Ubuntu, доставляет
исходники из этого проекта, запускает контейнер и проверяет `/health`.
Инвентарь, настройки, зависимости управляющей машины и пошаговый запуск
описаны в `ansible/README.md`. Данные реального сервера пока не заданы.

## Практики № 4 и № 5: Jenkins

`Jenkinsfile` получает код из GitHub, собирает образ с тестами и запускает
контейнер на Linux-агенте Jenkins. `Jenkinsfile.ansible` доставляет готовый
образ через `ansible/deploy_image.yml` на Ubuntu-сервер и проверяет запуск.
Создание задач, требования агента и настройка Credentials описаны в `ci/README.md`.
