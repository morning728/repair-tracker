"""Convert Jenkins parameters to structured inventory and deployment variables."""

import json
import os
from pathlib import Path
import re


def write_configuration(values, workspace):
    host = values.get('DEPLOY_HOST', '').strip()
    user = values.get('DEPLOY_USER', '').strip()
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]*', host):
        raise ValueError('SERVER_HOST: укажите IPv4 или DNS-имя сервера.')
    if not re.fullmatch(r'[a-z_][a-z0-9_-]*', user):
        raise ValueError('SERVER_USER: некорректное имя пользователя.')
    ssh_port = int(values.get('DEPLOY_SSH_PORT', '22'))
    app_port = int(values.get('DEPLOY_APP_PORT', '8080'))
    if not 1 <= ssh_port <= 65535 or not 1024 <= app_port <= 65535:
        raise ValueError('Проверьте SSH-порт и HTTP-порт.')
    image = values.get('REPAIR_IMAGE', '')
    if not re.fullmatch(r'repair-tracker:[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}', image):
        raise ValueError('Некорректный тег Docker-образа.')
    target = workspace / 'tmp'
    target.mkdir(parents=True, exist_ok=True)
    inventory = {'repair_servers': {'hosts': {'repair-server': {
        'ansible_host': host, 'ansible_user': user, 'ansible_port': ssh_port,
        'ansible_python_interpreter': '/usr/bin/python3',
    }}}}
    extra_vars = {'repair_image_ref': image,
                  'repair_image_archive': str((target / 'repair-image.tar').resolve()),
                  'repair_app_port': app_port}
    (target / 'jenkins-inventory.json').write_text(json.dumps(inventory, indent=2), encoding='utf-8')
    (target / 'deploy-vars.json').write_text(json.dumps(extra_vars, indent=2), encoding='utf-8')


if __name__ == '__main__':
    try:
        write_configuration(os.environ, Path.cwd())
    except (ValueError, TypeError) as error:
        raise SystemExit(str(error)) from None
    print('Jenkins inventory and deployment variables are ready.')
