FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ANSIBLE_COLLECTIONS_PATH=/opt/ansible/collections \
    ANSIBLE_CONFIG=/workspace/ansible/ansible.cfg

RUN apt-get update \
    && apt-get install -y --no-install-recommends openssh-client \
    && rm -rf /var/lib/apt/lists/*
COPY requirements-control.txt requirements.yml /tmp/ansible/
RUN pip install --no-cache-dir -r /tmp/ansible/requirements-control.txt \
    && ansible-galaxy collection install -r /tmp/ansible/requirements.yml -p /opt/ansible/collections

WORKDIR /workspace/ansible
ENTRYPOINT ["ansible-playbook"]
