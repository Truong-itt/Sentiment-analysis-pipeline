from utils import *
from logger import get_logger
from dotenv import load_dotenv
from schemas import News

load_dotenv()
logger = get_logger(logs_dir='/var/log/supervisor/tintucmoi/', log_filename='tintucmoi.log')
MONGO_DB = os.getenv("MONGO_DB")
MONGO_COLLECTION = os.getenv("MONGO_TTM__COLLECTION")

def main():
    pipeline = [
        {"$match": {"operationType": {"$in": ["insert", "update", "delete", "replace"]}}}
    ]
    full_document = 'updateLookup'
    while True:
        try:
            client = get_client_mongodb()
            if client is None:
                logger.error("Failed to connect to MongoDB")
                return
            db = client[MONGO_DB]
            collection = db[MONGO_COLLECTION]
            with collection.watch(pipeline=pipeline, full_document=full_document) as stream:
                logger.info("⚙️ Change Stream started. ")
                for change in stream:
                    logger.info(f"🔧 Change type: {change['operationType']}")
                    if change['operationType'] == 'insert' or change['operationType'] == 'update':
                        data = change.get('fullDocument', {})
                        if data.get('topic') == MONGO_COLLECTION:
                            logger.info(f"🔧 Processing ... ")
                            err = process_db(data, logger=logger)
                            if err:
                                logger.error(f"❌ Xử lý thất bại: {err} - link: {data.get('link')}")
                        if data=={} or not data.get('_id'):
                            logger.error(f"Unexpected error: {e} link: {data['link']}  id: {data.get('_id')}")
                            continue
        except Exception as e:
            logger.error(f"Unexpected error: {e} keyword: {data['keyword']}  id: {data.get('_id')}")
            client.close()
            pass

if __name__ == "__main__":
    main()
