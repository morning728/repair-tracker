"""Static validation; actual Ansible execution requires a Linux control node."""

from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess

import yaml
from jinja2 import Environment, StrictUndefined

ROOT = Path(__file__).resolve().parent


def check():
    documents = {}
    for path in ROOT.rglob('*.yml'):
        documents[path.relative_to(ROOT).as_posix()] = yaml.safe_load(path.read_text(encoding='utf-8'))
    play = documents['deploy.yml'][0]
    assert play['hosts'] == 'repair_servers' and play['become'] is True
    assert play['gather_facts'] is True
    def expanded_tasks(playbook):
        result = []
        for task in playbook.get('pre_tasks', []) + playbook['tasks']:
            if 'ansible.builtin.import_tasks' in task:
                result.extend(documents[task['ansible.builtin.import_tasks']])
            else:
                result.append(task)
        return result

    tasks = expanded_tasks(play)
    tasks += expanded_tasks(documents['deploy_image.yml'][0])
    for task in tasks:
        assert task.get('name'), 'Every task must have a name'
        assert any(key.startswith(('ansible.builtin.', 'community.docker.')) for key in task), task['name']
    copy_task = next(t for t in tasks if 'ansible.builtin.copy' in t)
    for source in copy_task['loop']:
        assert (ROOT.parent / source).exists(), f'Missing deployment source: {source}'
        assert source not in ('.git', '.venv', 'data', 'ansible'), source
    compose_task = next(t for t in tasks if 'community.docker.docker_compose_v2' in t)
    assert compose_task['community.docker.docker_compose_v2']['wait'] is True
    template = Environment(undefined=StrictUndefined).from_string(
        (ROOT / 'templates/compose.yaml.j2').read_text(encoding='utf-8'))
    variables = documents['group_vars/repair_servers.yml']
    rendered = template.render(**variables)
    compose = yaml.safe_load(rendered)
    assert compose['services']['web']['ports'] == ['127.0.0.1:8080:8000']
    assert compose['services']['web']['volumes'] == ['repair-data:/app/data']
    image_template = Environment(undefined=StrictUndefined).from_string(
        (ROOT / 'templates/compose.image.yaml.j2').read_text(encoding='utf-8'))
    image_compose = yaml.safe_load(image_template.render(**variables, repair_image_ref='repair-tracker:validation'))
    assert image_compose['services']['web']['image'] == 'repair-tracker:validation'
    assert 'build' not in image_compose['services']['web']
    image_task = next(t for t in expanded_tasks(documents['deploy_image.yml'][0])
                      if 'community.docker.docker_compose_v2' in t)
    assert image_task['community.docker.docker_compose_v2']['build'] == 'never'
    assert image_task['community.docker.docker_compose_v2']['pull'] == 'never'
    with TemporaryDirectory() as directory:
        output = Path(directory) / 'compose.yaml'
        output.write_text(rendered, encoding='utf-8')
        subprocess.run(['docker', 'compose', '-f', str(output), 'config', '--quiet'], check=True)
        output.write_text(image_template.render(**variables, repair_image_ref='repair-tracker:validation'), encoding='utf-8')
        subprocess.run(['docker', 'compose', '-f', str(output), 'config', '--quiet'], check=True)
    print('YAML, Jinja template, source files and Compose configuration: OK')
    print('This is a static check, not an ansible-playbook syntax check or deployment.')


if __name__ == '__main__':
    check()
