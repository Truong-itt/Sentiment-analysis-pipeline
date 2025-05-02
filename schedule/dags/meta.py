import os
import re
import json
import random
import logging
import requests
import pendulum
import feedparser
from time import sleep
from airflow import DAG
from logger import get_logger
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pymongo import MongoClient
from airflow.decorators import task
from datetime import datetime, timedelta
from utils import get_mongo_client, get_rss 
load_dotenv()

logger = get_logger(logs_dir='/var/log/rotoro_schedule/', log_filename='update_rotoro_db.log')

default_args = {
    'owner': 'social',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'daily_keyword_to_kafka',
    default_args=default_args,
    description='Chạy cách 8 tiếng một lần',
    schedule_interval='0 */8 * * *',
    start_date=datetime(2025, 1, 3, tzinfo=pendulum.timezone("Asia/Ho_Chi_Minh")),
    catchup=False,
) as dag:
    
    @task
    def get_data():
        try:
            logger.info("🟢 Bắt đầu lấy từ khóa từ RSS")
            rss_url = {
                "giaitri":"https://vnexpress.net/rss/giai-tri.rss",
                "kinhdoanh":"https://vnexpress.net/rss/kinh-doanh.rss",
                "tintucmoi":"https://vnexpress.net/rss/tin-moi-nhat.rss"
                }  
            news = get_rss(rss_url)
            logger.info(f"🟢 Đã gửi {len(news)} bài viết từ RSS vào mongo")
            return news
        except Exception as e:
            logger.error(f"🔴 Lỗi khi lấy dữ liệu từ RSS: {e}")
            raise
    get_data()
