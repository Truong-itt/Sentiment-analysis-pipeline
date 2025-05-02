FROM apache/airflow:2.10.4

WORKDIR /opt/airflow
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./dags /opt/airflow/dags
USER root
RUN mkdir -p /var/log/mention_schedule && \
    chown -R 1000:0 /var/log/mention_schedule && \
    chmod -R 755 /var/log/mention_schedule
USER airflow