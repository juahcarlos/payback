FROM ubuntu:22.04 AS production

RUN apt-get update && apt-get install -y cron bash
RUN apt-get update && apt-get install -y dnsutils
RUN getent group www-data || groupadd -r www-data && \
    id -u www-data || useradd -r -g www-data -s /usr/sbin/nologin www-data

RUN apt-get update && apt-get install -y python3-pip
RUN pip3 install --no-cache-dir --upgrade pip
RUN pip3 install --no-cache-dir poetry
RUN poetry config virtualenvs.create false

WORKDIR /ws
COPY config.py config.py
COPY setup.cfg setup.cfg
COPY pyproject.toml pyproject.toml
COPY crontabs crontabs/
COPY libs libs/
COPY langs langs/
COPY dbm dbm/
COPY grpc_lib grpc_lib/
RUN poetry install
WORKDIR /ws/crontabs
RUN touch /var/log/cron.log && chmod 0666 /var/log/cron.log
RUN mkdir -p /var/run && chown www-data:www-data /var/run
RUN touch /var/log/cron.log && chown www-data:www-data /var/log/cron.log
COPY crontabs/crontab /etc/cron.d/appcron
RUN chmod 0644 /etc/cron.d/appcron
RUN poetry install --no-root

CMD ["cron", "-f"]