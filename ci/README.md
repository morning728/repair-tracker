# Практики Jenkins и Jenkins + Ansible

## Стенд

GitHub хранит приложение, Dockerfile, Jenkinsfile и плейбуки. Jenkins-агент
получает код и собирает образ. Ubuntu-сервер принимает приложение через SSH.
«Сервер» может быть VM на личном компьютере; контейнер запускается уже на нём.
Одну VM можно использовать для всех практик развёртывания.

Нужен работающий Jenkins и Linux-агент с меткой `docker-linux`. На агенте
должны быть Git, Python 3.12+, venv, SSH-клиент, Docker и Compose v2.18+.
Пользователь агента должен иметь доступ к Docker. Плагины Jenkins: Pipeline,
Git, Credentials Binding, SSH Agent. Обычный Windows-агент не подходит:
Jenkinsfile используют `sh` и Linux-окружение.

Dockerfile запускает тесты при сборке и содержит healthcheck. Архитектура
агента и сервера должна совпадать; для обычного ПК используется amd64.
Агенту нужен доступ к GitHub, Docker Hub, PyPI и Ansible Galaxy.

## Практика № 4

1. Создайте Pipeline job `repair-tracker-local`.
2. Definition → Pipeline script from SCM, SCM → Git.
3. Repository URL: `https://github.com/morning728/repair-tracker.git`.
4. Branch Specifier: `*/master`, Script Path: `Jenkinsfile`.
5. Для приватного репозитория выберите credential доступа к GitHub.
6. Сохраните и нажмите Build Now.

Этапы: получение кода → Docker build с тестами → Compose up → HTTP health.
Параметр APP_PORT по умолчанию равен 8081. Контейнер остаётся работать на
Jenkins-агенте по http://localhost:8081, данные находятся в отдельном томе
проекта `repair-tracker-ci`. Для удалённого агента используйте SSH-туннель.

Две задачи с одним Compose-проектом не должны работать одновременно.
`disableConcurrentBuilds` защищает от этого внутри одной задачи. Конвейеры
рассчитаны на обычные Pipeline jobs, а не параллельный деплой всех веток.

## Практика № 5

Создайте вторую Pipeline job `repair-tracker-server` с теми же SCM и веткой,
но Script Path: `Jenkinsfile.ansible`.

Конвейер собирает образ с тегом из номера сборки и Git SHA, сохраняет его
через `docker image save` и вызывает `ansible/deploy_image.yml`. Плейбук
копирует архив на сервер, загружает образ, проверяет архитектуру, запускает
Compose и `/health`. На сервере не выполняется повторная сборка приложения
и не используется реестр образов.

Настройте Jenkins Credentials:

| ID | Тип | Значение |
| --- | --- | --- |
| repair-server-ssh | SSH Username with private key | Пользователь и ключ доступа к Ubuntu VM; допускается passphrase |
| repair-server-known-hosts | Secret file | known_hosts с проверенным публичным ключом SSH-сервера |
| repair-server-sudo | Secret text, необязательно | Пароль sudo пользователя VM |

Ключ сервера сверьте по `/etc/ssh/ssh_host_ed25519_key.pub` в консоли VM.
Проверка host key включена. Ключ доступа к VM и ключ GitHub не обязательно
один и тот же. Публичный ключ VM-доступа должен быть в её authorized_keys.
Приватные ключи и пароли задаются через Jenkins Credentials, не через Git.

В Build with Parameters укажите SERVER_HOST (IP), SERVER_USER, SERVER_SSH_PORT
(обычно 22) и SERVER_APP_PORT (8080). Credential IDs по умолчанию совпадают
с таблицей. SERVER_SUDO_CREDENTIAL_ID оставьте пустым при sudo без пароля,
иначе укажите `repair-server-sudo`. Пароль передаётся через окружение;
генерируемые JSON-файлы содержат только lookup переменной, не сам пароль.

При первом запуске Jenkins читает параметры из SCM. Пустой SERVER_HOST
приведёт к остановке до сборки; повторите Build with Parameters с настоящим IP.

Серверу нужен доступ к Docker APT-репозиторию для первой установки Docker,
но не к Docker Hub или PyPI для сборки приложения. Открытие результата:

```bash
ssh -N -L 8082:127.0.0.1:8080 USER@SERVER_IP
```

Адрес: http://localhost:8082. Данные используют тот же том, что в практике
Ansible, поэтому переход на готовый образ сохраняет заявки.

## Проверки

```bash
python -m unittest discover -s tests -v
python ansible/check_config.py
```

Проверка Ansible в Linux-контейнере с Windows, из корня проекта:

```powershell
docker build -f ansible/controller.Dockerfile -t repair-ansible:local ansible
docker run --rm --mount "type=bind,source=$PWD,target=/workspace,readonly" repair-ansible:local -i inventory.ini.example deploy.yml --syntax-check
docker run --rm --mount "type=bind,source=$PWD,target=/workspace,readonly" repair-ansible:local -i inventory.ini.example deploy_image.yml -e repair_image_ref=repair-tracker:validation -e repair_image_archive=/workspace/tmp/repair-image.tar --syntax-check
```

Это не развёртывает приложение на сервере. Jenkins Pipeline DSL проверяется
и выполняется в Jenkins, локальный YAML-парсер не заменяет эту проверку.

## Демонстрация

Показать Dockerfile, Jenkinsfile и плейбук в GitHub, зелёные стадии Jenkins,
Console Output, тег образа с Git SHA, результат Ansible и работающую форму.
Проверить сохранение заявок после повторного развёртывания.

Архив образа остаётся в workspace. SHA256 и metadata образа сохраняются как
небольшие артефакты сборки. Обслуживание старых образов и архивов выполняется
отдельно; конвейер не удаляет чужие образы или тома данных.

Документация:

- https://www.jenkins.io/doc/book/pipeline/getting-started/
- https://www.jenkins.io/doc/book/pipeline/syntax/
- https://www.jenkins.io/doc/pipeline/steps/credentials-binding/
- https://docs.ansible.com/projects/ansible/latest/collections/community/docker/docker_image_load_module.html
