FROM postgres:14

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    libpq-dev \
    gcc \
    python3-venv \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Tạo và kích hoạt môi trường ảo để tránh lỗi externally-managed-environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir psycopg2-binary patroni[etcd]
RUN rm -rf /var/lib/postgresql/data

RUN mkdir -p /var/lib/postgresql/data
RUN chown -R postgres:postgres /var/lib/postgresql
RUN chmod -R 700 /var/lib/postgresql/data

# COPY patroni.yml /etc/patroni.yml
USER postgres
CMD ["patroni", "/etc/patroni.yml"]