# Практическая работа № 5

## Jenkins, Ansible и доставка Docker-образа

### Задание

Дополнить Pipeline из практической работы № 4 вызовом Ansible для отправки собранного Docker-образа на «сервер» и развёртывания приложения на нём.

### Требования

Pipeline должен:

1. получить исходный код приложения из GitHub;
2. собрать Docker-образ;
3. подготовить образ к передаче на сервер;
4. вызвать Ansible для отправки образа;
5. развернуть приложение на сервере;
6. проверить доступность запущенного приложения.

Ansible-плейбук должен изначально находиться в репозитории GitHub.

### Результат

После выполнения Pipeline Docker-образ должен быть доставлен на сервер, а приложение — запущено и доступно для проверки.

В репозитории должны находиться Jenkins Pipeline, Ansible-плейбук и необходимые файлы конфигурации.

### Запуск и проверка на macOS и Windows

Jenkins job создаётся как `Pipeline script from SCM` с веткой `*/master` и
Script Path `Jenkinsfile.ansible`. Сам Pipeline работает на Linux-агенте с
меткой `docker-linux`; macOS и Windows используются как хосты Docker Desktop
и Jenkins-контроллера.

Перед запуском создайте в Jenkins credentials: `repair-server-ssh` (SSH-ключ),
`repair-server-known-hosts` (Secret file) и при необходимости
`repair-server-sudo` (Secret text). В **Build with Parameters** укажите
фактические `SERVER_HOST`, `SERVER_USER`, `SERVER_SSH_PORT` и
`SERVER_APP_PORT`. Значения по умолчанию намеренно не содержат IP, ключей или
паролей.

Если Jenkins запущен в Docker Desktop, а Ubuntu VM Multipass доступна только
хостовой ОС, Linux-контейнер может не видеть её приватный IP. В этом случае
используйте `ci/ssh-bastion.Dockerfile`: он создаёт изолированный SSH-посредник
в Docker-сети Jenkins. У job задаются `DEFAULT_SERVER_HOST=repair-jenkins-bastion`
и `DEFAULT_SERVER_SSH_PORT=2223`; macOS-хост создаёт обратный SSH-туннель к VM.
Такой вариант не изменяет Wi-Fi, маршрутизацию macOS или сеть Multipass.

Успешный Console Output должен показать: сборку образа, сохранение
`repair-image.tar`, запуск `ansible/deploy_image.yml` и результат HTTP-проверки
`/health` на Ubuntu-сервере. Учебная конфигурация публикует приложение в сети
VM, поэтому при доступности её адреса откройте `http://SERVER_IP:8080` и
`http://SERVER_IP:8080/health`. Для изолированного сервера проверьте
приложение через SSH-туннель:

```bash
ssh -N -L 8082:127.0.0.1:8080 USER@SERVER_IP
```

Откройте `http://127.0.0.1:8082/health`; ожидаемый ответ — `{"status":"ok"}`.

### Демонстрация автоматического запуска

В настроенном учебном стенде job `repair-tracker-practice-5` отслеживает ветку
`prac5-mac` с помощью опроса Git раз в минуту. Чтобы показать полный цикл,
внесите небольшое изменение в проект, создайте commit и отправьте его в эту
ветку:

```bash
git add <изменённые_файлы>
git commit -m "Добавил изменение для демонстрации"
git push origin prac5-mac
```

Не нажимайте **Build Now**: Jenkins сам обнаружит новый commit в течение
минуты. В Console Output новой сборки покажите строки `Started by an SCM
change`, `Checking out Revision`, `PLAY RECAP` без ошибок и `Finished:
SUCCESS`.

До доступа к серверу можно проверить оба плейбука в Linux-контейнере. На
macOS/Linux из корня репозитория:

```bash
docker build -f ansible/controller.Dockerfile -t repair-ansible:local ansible
docker run --rm --mount "type=bind,source=$PWD,target=/workspace,readonly" repair-ansible:local -i inventory.ini.example deploy.yml --syntax-check
docker run --rm --mount "type=bind,source=$PWD,target=/workspace,readonly" repair-ansible:local -i inventory.ini.example deploy_image.yml -e repair_image_ref=repair-tracker:validation -e repair_image_archive=/workspace/tmp/repair-image.tar --syntax-check
```

В Windows PowerShell замените источник bind mount на абсолютный путь:

```powershell
docker build -f ansible/controller.Dockerfile -t repair-ansible:local ansible
docker run --rm --mount "type=bind,source=$($PWD.Path),target=/workspace,readonly" repair-ansible:local -i inventory.ini.example deploy.yml --syntax-check
docker run --rm --mount "type=bind,source=$($PWD.Path),target=/workspace,readonly" repair-ansible:local -i inventory.ini.example deploy_image.yml -e repair_image_ref=repair-tracker:validation -e repair_image_archive=/workspace/tmp/repair-image.tar --syntax-check
```

Синтаксическая проверка не подключается к серверу. Реальное выполнение требует
доступного Ubuntu-сервера, SSH-ключа и корректного known_hosts.
