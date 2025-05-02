FROM python:3.10.5-slim-buster

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get -y update && apt-get -y upgrade
RUN apt-get -y install supervisor

COPY ./requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /process
COPY ./process .
# RUN rm -f /var/log/supervisor/*

# RUN mkdir -p /var/log/supervisor/kinhdoanh \
#              /var/log/supervisor/giaitri \
#              /var/log/supervisor/tintucmoi \
#              /var/log/supervisor/initializeDB

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]