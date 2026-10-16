FROM jenkins/jenkins:lts-jdk21

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git python3 python3-venv \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc \
    && chmod a+r /etc/apt/keyrings/docker.asc \
    && printf 'deb [arch=%s signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian trixie stable\n' "$(dpkg --print-architecture)" > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends docker-ce-cli docker-compose-plugin \
    && rm -rf /var/lib/apt/lists/*

RUN jenkins-plugin-cli --plugins workflow-aggregator git credentials-binding ssh-agent

COPY jenkins-init.groovy /usr/share/jenkins/ref/init.groovy.d/jenkins-init.groovy

USER jenkins
