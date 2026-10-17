FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install --no-install-recommends --yes openssh-server \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash tunnel \
    && install --directory --mode 0700 --owner tunnel --group tunnel /home/tunnel/.ssh \
    && install --directory --mode 0755 /run/sshd

RUN printf '%s\n' \
    'PasswordAuthentication no' \
    'PermitRootLogin no' \
    'AllowTcpForwarding yes' \
    'GatewayPorts clientspecified' \
    'X11Forwarding no' \
    > /etc/ssh/sshd_config.d/jenkins-tunnel.conf

EXPOSE 22

CMD ["/bin/sh", "-c", "ssh-keygen -A && exec /usr/sbin/sshd -D -e"]
