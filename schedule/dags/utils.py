from pymongo import MongoClient
from logger import get_logger
import os
import logging
from dotenv import load_dotenv
import re
import requests
from time import sleep
import random
from bs4 import BeautifulSoup
import feedparser
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import pytz
from concurrent.futures import as_completed

load_dotenv()
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_HOST = os.getenv("MONGO_HOST")
MOGO_DB = os.getenv("MOGO_DB")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION")
OPTIONS=os.getenv("OPTIONS")
MAX_WORKERS=os.getenv("MAX_WORKERS", 5)
API_SENTIMENT= os.getenv("API_SENTIMENT")
logger = get_logger(logs_dir='/var/log/rotoro_schedule/', log_filename='update_rotoro_db.log')
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

def get_mongo_client():
    """
    Kết nối đến MongoDB với thông tin từ biến môi trường.
    """
    try:
        client = MongoClient(f'mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}/{OPTIONS}')
        client.admin.command('ping')
        return client
    except Exception as e:
        return False

def get_content(new):
    try:
        response = requests.get(new['link'], headers=headers)
        sleep(random.randint(1, 3))
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')
        content = ""
        for p in paragraphs:
            content += p.get_text() + "\n"
        cleaned_text = re.sub(r'\s+', ' ', content)  
        cleaned_text = cleaned_text.strip() 
        new['content'] = cleaned_text
        logger.info(f"🟢 Đã lấy nội dung từ link: {new['link']}")
        return new
    except Exception as e:
        logger.error(f"🔴 Lỗi khi lấy nội dung từ link: {new['link']}: {e}")
        return ""  

def get_rss(rss_url):
    api_sentiment = os.getenv("API_SENTIMENT")

    feeds = [{key: feedparser.parse(value)} for key, value in rss_url.items()]
    sleep(1)
    news = []
    time_format = '%a, %d %b %Y %H:%M:%S %z'
    for feed in feeds:
        for key, parsed_feed in feed.items():
            for entry in parsed_feed.entries:
                if entry.title and entry.link and entry.published and entry.summary:
                    soup = BeautifulSoup(entry.summary, 'html.parser')
                    summary = soup.get_text(strip=True)
                    dt = datetime.strptime(entry.published, time_format)
                    dt = dt.replace(tzinfo=pytz.timezone("Asia/Ho_Chi_Minh")) 
                    temp = {
                        'title': entry.title,
                        'link': entry.link,
                        'published': dt,
                        'summary': summary,
                        'topic': key
                    }
                    news.append(temp)
    logger.info(f"🟢 Hoàn thành lấy dư liệu cơ bản tiến hành lấy content...")
    try:
        logger.info(f"🟢 Đang lấy dữ liệu content")
        client = get_mongo_client()
        if not client:
            logger.error("🔴 Không thể kết nối MongoDB để lưu content từng bài")
            return news 

        db = client[MOGO_DB]
        logger.info(f"🟢 Đang lấy dữ liệu content và lưu dần vào MongoDB")
        with ThreadPoolExecutor(max_workers=int(MAX_WORKERS)) as executor:
            future_to_news = {executor.submit(get_content, new): new for new in news}
            for future in as_completed(future_to_news):
                try:
                    result = future.result()
                    try:
                        payload = {"text": f"{result['title']} - {result['summary']}", "entity": f"{result['topic']}"}
                        response = requests.post(api_sentiment, json=payload,timeout=10)
                        result['sentiment'] = response.json()['sentiment']
                    except Exception as e:
                        logger.error(f"🔴 Lỗi khi gọi API sentiment")
                    if result and isinstance(result, dict):
                        logger.info(f"topic {result['topic']} link {result['link']}")
                        db[result['topic']].update_one(
                            {'link': result['link']},
                            {'$set': result},
                            upsert=True
                        )
                        logger.info(f"✅ Đã lưu bài viết {result['title']} setiment: {result['sentiment']} vào MongoDB topic: {result['topic']}")
                except Exception as e:
                    logger.error(f"❌ Lỗi khi xử lý bài viết: {e}")
        client.close()
        logger.info("🟢 Đã xử lý và lưu toàn bộ bài viết thành công")
        return news        
    except Exception as e:  
        logger.error(f"🔴 Lỗi khi lấy dữ liệu content: {e}")
        raise
    
