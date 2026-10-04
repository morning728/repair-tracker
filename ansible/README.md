# Практическая работа № 3: развёртывание через Ansible

`deploy.yml` доставляет приложение из работы № 2 на Ubuntu-сервер и запускает
его в Docker. Сервер пока не задан: `inventory.ini.example` содержит пример,
а не действующие данные подключения.

## Что выполняет плейбук

1. Проверяет Ubuntu 22.04/24.04, архитектуру amd64/arm64 и настройки.
2. Настраивает официальный APT-репозиторий Docker и устанавливает Engine/Compose.
3. Запускает Docker и включает запуск при загрузке сервера.
4. Копирует исходники, шаблоны, статику и тесты из локального проекта в `/opt/repair-tracker`.
5. Формирует серверный Compose-файл и собирает контейнер. Dockerfile запускает тесты.
6. Запускает сервис и ожидает состояния healthy.
7. Проверяет HTTP `/health` и состояние базы приложения.

GitHub-ключи на сервер не копируются. Исходники доставляются с управляющей
машины, поэтому серверу не нужен доступ к GitHub, включая приватный репозиторий.
Он должен иметь доступ к репозиторию Docker, Docker Hub и PyPI для установки
пакетов и сборки образа. Рекомендуется свежая Ubuntu без конфликтующих пакетов
`docker.io`, `podman-docker` и отдельно установленного `containerd`.

## Где запускать Ansible

Ansible запускается на управляющей Linux-машине с Python 3.12 или новее.
Для лабораторной работы можно использовать Ubuntu в WSL или отдельную VM.
Сервер назначения должен иметь Python 3, SSH и пользователя с sudo.
Docker Desktop на Windows для этого сценария не нужен: контейнер работает
на Ubuntu-сервере.

В терминале управляющей машины:

```bash
sudo apt update
sudo apt install -y python3 python3-venv git openssh-client
git clone https://github.com/morning728/repair-tracker.git
cd repair-tracker
python3 -m venv .ansible-venv
source .ansible-venv/bin/activate
python -m pip install -r ansible/requirements-control.txt
cd ansible
ansible-galaxy collection install -r requirements.yml
cp inventory.ini.example inventory.ini
```

Если репозиторий приватный, клонируйте его с авторизацией или скопируйте
проект на управляющую машину. В WSL разместите проект в домашнем каталоге
Linux: Ansible может игнорировать конфигурацию в каталогах Windows с
разрешением записи для всех. Среда Ansible не должна входить в Git.

## Настройка сервера

Отредактируйте `inventory.ini`: замените `192.0.2.10` на реальный IP, `ubuntu`
на SSH-пользователя и `~/.ssh/repair_server` на путь к его ключу. Это ключ
доступа к серверу, а не автоматически ключ GitHub. Файл inventory исключён
из Git.

Сначала выполните обычное SSH-подключение, проверьте отпечаток сервера и
убедитесь, что пользователь имеет sudo:

```bash
ssh -i ~/.ssh/repair_server ubuntu@SERVER_IP
sudo -v
exit
```

Затем из каталога `ansible`:

```bash
ansible repair_servers -m ansible.builtin.ping
ansible-playbook deploy.yml --syntax-check
ansible-playbook deploy.yml --ask-become-pass
```

Если sudo работает без пароля, параметр `--ask-become-pass` можно убрать.
Если ключ защищён паролем, предварительно добавьте его в `ssh-agent`.
Проверка ключей серверов включена; пароли в inventory сохранять не требуется.

## Открытие приложения

По умолчанию порт 8080 доступен только на самом сервере. Для просмотра
с компьютера откройте SSH-туннель:

```bash
ssh -N -L 8080:127.0.0.1:8080 -i ~/.ssh/repair_server ubuntu@SERVER_IP
```

Откройте http://localhost:8080, оставив туннель работающим. Если локальный порт
занят, используйте `-L 8081:127.0.0.1:8080` и http://localhost:8081.

Для сервера в изолированной учебной сети можно задать
`repair_bind_address: 0.0.0.0` в `group_vars/repair_servers.yml`, тогда приложение
будет доступно по `http://SERVER_IP:8080` при разрешении порта в сети.
Приложение не содержит авторизации; для открытого интернет-сервера используйте
режим по умолчанию и SSH-туннель.

## Повторный запуск и данные

Повторите ту же команду `ansible-playbook deploy.yml`, чтобы применить изменения.
Копирование сравнивает содержимое, а пересборка выполняется при изменении
исходников или серверной конфигурации. Compose проверяет состояние контейнера
при каждом запуске. SQLite сохраняется в Docker volume и не заменяется при
доставке исходников. Плейбук не удаляет тома.

Итоговое подтверждение выполнения на сервере:

```bash
sudo docker compose -f /opt/repair-tracker/compose.yaml ps
curl http://127.0.0.1:8080/health
```

Ожидается контейнер healthy и JSON `{"status":"ok"}`. Второй прогон плейбука
при отсутствии внешних изменений должен обходиться без пересборки образа.

## Что проверено без сервера

Локальный скрипт проверяет YAML, рендеринг Jinja, наличие доставляемых файлов
и синтаксис сформированного Compose. Он не заменяет `ansible-playbook
--syntax-check` и реальный прогон на Ubuntu:

```bash
python -m pip install -r requirements-check.txt
python check_config.py
```

Проверка Ansible в Linux-контейнере с Windows описана в `../ci/README.md`.
Реальный прогон `deploy.yml` требует настройки inventory и SSH-доступа.

## Доставка готового образа из Jenkins

Для следующей практики добавлен `deploy_image.yml`. Он использует ту же
подготовку Ubuntu и проверку HTTP, но вместо исходников доставляет архив
образа, загружает его в Docker и запускает без повторной сборки.
Пример ручного вызова с Linux-управляющей машины:

```bash
docker image save -o /tmp/repair-image.tar repair-tracker:validation
ansible-playbook deploy_image.yml --ask-become-pass \
  -e repair_image_ref=repair-tracker:validation \
  -e repair_image_archive=/tmp/repair-image.tar
```

Образ предварительно должен быть собран с указанным тегом. Автоматическое
сохранение и вызов плейбука реализованы в `../Jenkinsfile.ansible`.

## Объяснение для зачёта

Inventory описывает сервер и SSH-подключение. `group_vars` содержит путь,
порт и параметры публикации. Модули Ansible приводят сервер к нужному
состоянию. `become` выполняет установку и запуск Docker через sudo.
`copy` доставляет приложение, `template` формирует Compose,
`community.docker.docker_compose_v2` управляет сервисом, `uri` подтверждает
HTTP-доступность после запуска.

Документация:

- https://docs.docker.com/engine/install/ubuntu/
- https://docs.ansible.com/projects/ansible/latest/collections/community/docker/docker_compose_v2_module.html
- https://docs.ansible.com/projects/ansible/latest/installation_guide/intro_installation.html
