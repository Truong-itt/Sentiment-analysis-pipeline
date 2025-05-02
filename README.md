# Sentiment Analysis Data Pipeline

This project implements a high-availability data pipeline for crawling data, performing sentiment analysis using a local Vietnamese model, and streaming processed data to MongoDB and PostgreSQL. The entire system is containerized using Docker, with Airflow for orchestration, MongoDB Replica Set for high availability, and PostgreSQL HA using Patroni, etcd, and HAProxy.

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
- [Running the Pipeline](#running-the-pipeline)
- [Environment Variables](#environment-variables)

## Overview
This pipeline:
1. Uses **Apache Airflow** to schedule and orchestrate data crawling tasks.
2. Crawls data from specified sources and processes it for sentiment analysis.
3. Performs sentiment analysis using the local **Khoa/vietnamese-sentiment-analysis-with-entity** model.
4. Stores processed data in a **MongoDB Replica Set** for high availability.
5. Streams data from MongoDB to a **PostgreSQL HA** cluster (using Patroni, etcd, and HAProxy).
6. Runs entirely in **Docker** containers for portability and scalability.

## Architecture
The system consists of the following components:
- **Airflow**: Orchestrates the pipeline, scheduling data crawling and processing tasks.
- **Crawler**: Custom script to fetch data from specified sources.
- **Sentiment Analysis Model**: Local `Khoa/vietnamese-sentiment-analysis-with-entity` model for analyzing text sentiment.
- **MongoDB Replica Set**: Stores processed data with high availability (3-node replica set).
- **MongoDB to PostgreSQL Stream**: Streams data from MongoDB collections to PostgreSQL using a custom connector.
- **PostgreSQL HA Cluster**: High-availability PostgreSQL setup with Patroni, etcd (for consensus), and HAProxy (for load balancing).
- **Docker**: Containerizes all components for consistent deployment.

## Prerequisites
- **Docker** and **Docker Compose** installed.
- Git installed for cloning the repository.
- Minimum hardware: 16GB RAM, 4 CPU cores, 50GB free disk space.
- Python 3.9+ (for local development or testing outside Docker).

## Setup Instructions
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Truong-itt/sentiment-analysis-pipeline.git
   cd sentiment-analysis-pipeline
   ```

2. **Configure Environment Variables**:
   Copy the `.env.example` file to `.env` and update the values:
   ```bash
   cp .env.example .env
   nano .env
   ```
3. **Download model AI sentiment**:

   ##### Download file: https://huggingface.co/Khoa/vietnamese-sentiment-analysis-with-entity/tree/main
   ##### Move all  file model in foder sentiment_model
   
   ```bash
   cd sentiment_api
   mkdir sentiment_model
   mv /path/to/downloaded/files/* sentiment_model/
   ```

4. **Docker network Containers**:
   ```bash
   docker network create mongo_replica_rtr
   docker network create postgres-ha
   ```

## Running the Pipeline
1. **Start the Pipeline**:
   Access in foder database, datalake, sentiment_api, schedule, transform,gui 

   ```bash
   docker compose up -d --build
   ```

2. **Access UI**:
   - Airflow: `http://localhost:8090`
   - Login: `rotoro/airflow`
   - Portainer: `http://localhost:9005`
   - Mongo express: `http://localhost:8091`
   - Supervisor UI: `http://localhost:9001`
   - HAProxy: `http://localhost:7000/stats`
   
2. **Access host**:
   - Posgres haproxy in docker and out localhost (5000:master write master, 5001 read replica)
   - User Posgres: postgres/postgres
   - Mongo mongo1, mongo2, mongo3 in docker and out localhost (mongo1:27017,mongo2:27018,mongo3:27019)
   - User Mongo: rotoro/rotoro123

3. **Stop the Pipeline**:
   Access in foder database, datalake, sentiment_api, schedule, transform, gui 

   ```bash
   docker-compose down
   ```


