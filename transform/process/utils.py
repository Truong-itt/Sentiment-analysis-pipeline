import os
import requests
import psycopg2
import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta
from glob import glob
from psycopg2 import extras
from dotenv import load_dotenv
from logger import get_logger
from schemas import News

# logger = get_logger(logs_dir='/var/log/supervisor/facebook/', log_filename='facebook.log')

load_dotenv()
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT_MASTER = os.getenv("POSTGRES_PORT_MASTER")
POSTGRES_PORT_SLAVE = os.getenv("POSTGRES_PORT_SLAVE")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
URI_MONGO = os.getenv("URI_MONGO")

DECODE = {
    "NEU": 0,
    "POS": 1,
    "NEG": 2
}

def get_client_mongodb():
    """
    Kết nối tới MongoDB.
    """
    try:
        client = MongoClient(URI_MONGO, serverSelectionTimeoutMS=5000)
        return client
    except:
        return None

def scores(sentiment):
    if sentiment == "NEUTRAL":
        return 1
    elif sentiment == "POSITIVE":
        return 2
    elif sentiment == "NEGATIVE":
        return 3
    else:
        return None
    
def schemas_dbs(data):
    temp = scores(data.get('sentiment'))
    if temp == False:
        return None 
    post_data = News(
        link=data.get('link'),
        content=data.get('content'),
        published=data.get('published'),
        sentiment=data.get('sentiment'),
        sentiment_score=temp,
        summary=data.get('summary'),
        title=data.get('title'),
        topic=data.get('topic')
    )
    
    return post_data

def process_db(data, logger):
    try:
        db = Postgres()
        if not db.is_connected():
            logger.erorr("❌ Không thể kết nối đến Postgres")
            return
        news_obj = schemas_dbs(data)
        data_tuple = (
            news_obj.link,
            news_obj.content,
            news_obj.published,
            news_obj.sentiment,
            news_obj.sentiment_score,
            news_obj.summary,
            news_obj.title,
            news_obj.topic
        )
        if data_tuple is None:
            logger.info("🔴 Dữ liệu không hợp lệ (không phân loại sentiment)")
            return
        returned_id = db.upsert('news_articles', tuple(data_tuple), ['link'])
        db.close()
        if returned_id is None:
            msg = "🔴 Upsert thất bại, không trả về ID"
            logger.error(msg)
            return 
        logger.info(f"🔧 Đã upsert thành công: {returned_id} bai viết: {news_obj.link}")
        return   
    except Exception as e:
        if logger: logger.error(f"❌ Lỗi không xác định trong process_db: {e}")
        db.close()
        return 
    
class Postgres:
    def __init__(self):
        self.host = POSTGRES_HOST
        self.user = POSTGRES_USER
        self.password = POSTGRES_PASSWORD
        self.db = POSTGRES_DB
        self.port_master = POSTGRES_PORT_MASTER
        self.port_slave = POSTGRES_PORT_SLAVE
        self.write_conn = None
        self.read_conn = None
        self.write_cursor = None
        self.read_cursor = None
        self.connect()

    def connect(self):
        try:
            self.write_conn = psycopg2.connect(
                host=self.host,
                port=self.port_master,
                user=self.user,
                password=self.password,
                dbname=self.db
            )
            self.write_cursor = self.write_conn.cursor(cursor_factory=extras.DictCursor)
            self.read_conn = psycopg2.connect(
                host=self.host,
                port=self.port_slave,
                user=self.user,
                password=self.password,
                dbname=self.db
            )
            self.read_cursor = self.read_conn.cursor(cursor_factory=extras.DictCursor)
        except Exception as e:
            print(f"❌ Lỗi khi kết nối PostgreSQL: {e}")
            raise

    def execute_write(self, query, data=None):
        try:
            self.write_cursor.execute(query, data)
            self.write_conn.commit()
        except Exception as e:
            self.write_conn.rollback()
            print(f"❌ Lỗi khi ghi dữ liệu: {e}")
            raise

    def execute_read(self, query, data=None):
        try:
            self.read_cursor.execute(query, data)
            return self.read_cursor.fetchall()
        except Exception as e:
            print(f"❌ Lỗi khi đọc dữ liệu: {e}")
            raise

    def close(self):
        if self.write_cursor: self.write_cursor.close()
        if self.write_conn: self.write_conn.close()
        if self.read_cursor: self.read_cursor.close()
        if self.read_conn: self.read_conn.close()

    def is_connected(self):
        try:
            self.write_cursor.execute("SELECT 1;")
            self.read_cursor.execute("SELECT 1;")
            return True
        except Exception:
            return False
        
    def run_sql_file(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                sql = f.read()
            self.write_cursor.execute(sql) 
            self.write_conn.commit()
            print(f"✅ Thực thi file SQL thành công: {file_path}")
        except Exception as e:
            self.write_conn.rollback()
            print(f"❌ Lỗi khi chạy file SQL: {e}")
            raise

    def get_columns(self, table_name):
        self.write_cursor.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        return [row[0] for row in self.write_cursor.fetchall()]

    def upsert(self, table_name: str, data: tuple, ids: list = [], updates: list = None):
        conflict_target = 'id'
        update_cols = self.get_columns(table_name)
        update_cols.remove(conflict_target)

        check_ids = [str(data[update_cols.index(id)]).replace("'", "''") for id in ids]
        updates_clause = ', '.join([f"{col} = EXCLUDED.{col}" for col in update_cols]) if updates is None else updates

        try:
            where_clause = ' AND '.join([f"{col} = '{val}'" for col, val in zip(ids, check_ids)])
            sql_exists = f"SELECT {conflict_target} FROM {table_name} WHERE {where_clause}"
            self.write_cursor.execute(sql_exists)
            result = self.write_cursor.fetchone()

            attrs = tuple(update_cols)
            if result:
                _id = result[0]
                data = (_id,) + data
                attrs = (conflict_target,) + attrs

            sql_insert = f"""
                INSERT INTO {table_name} ({','.join(attrs)})
                VALUES ({','.join(['%s']*len(attrs))})
                ON CONFLICT ({conflict_target})
                DO UPDATE SET {updates_clause}
                RETURNING id;
            """

            self.write_cursor.execute(sql_insert, data)
            returned_id = self.write_cursor.fetchone()[0]
            self.write_conn.commit()
            return returned_id
        except Exception as e:
            self.write_conn.rollback()
            print(f"❌ Lỗi khi upsert vào bảng `{table_name}`: {e}")
            return None

    
# def read_json_file(file_path):
#     with open(file_path, 'r', encoding='utf-8') as file:
#         data = json.load(file)
#     return data

# def pretty_json(data):
#     print(json.dumps(data, indent=4))

# def batch(iterable, n=128):
    # iterable = iter(iterable)
    # while batch := list(islice(iterable, n)):
    #     yield batch

    # def query(self, sql_query, fetch=True):
    #     try:
    #         self.cursor.execute(sql_query)
    #         if fetch:
    #             rows = self.cursor.fetchall()
    #             df = pd.DataFrame(rows, columns=[desc[0] for desc in self.cursor.description])
    #             return df
    #         else:
    #             self.conn.commit()
    #             return None  
    #     except Exception as e:
    #         self.cursor.execute("ROLLBACK")
    #         print(f'❌ ROLLBACK: {e}')
    # def delete_table(self, table_names:list=[]):
    #     for table in table_names:
    #         try:
    #             self.cursor.execute(f"DROP TABLE {table}")
    #             print(f"🗑 Deleted {table}")
    #         except Exception as e:
    #             self.cursor.execute("ROLLBACK")
    #             print(f'❌ ROLLBACK: {e}')
    #     self.conn.commit()
    
    # def upsert(self, table_name:str, data:tuple, ids:list=[], updates:list=None):
    #     conflict_target = 'id'
    #     update_cols = self.get_columns(table_name) # Get all columns
    #     update_cols.remove(conflict_target) # Remove primary key
    #     check_ids = [data[update_cols.index(id)].replace("'", "''") for id in ids] 
    #     updates = ','.join([f"{c}={'EXCLUDED.'+c}" for c in update_cols]) if updates is None else updates # Default update all columns except primary key
    #     try:
    #         sql_exists = f"SELECT {conflict_target} FROM {table_name} WHERE {' AND '.join([f'''{id} = '{c_id}'; ''' for id, c_id  in zip(ids, check_ids)])}"
    #         self.cursor.execute(sql_exists)
    #         result = self.cursor.fetchone()
    #         attrs = tuple(update_cols)
    #         if result:
    #             _id = result[0]
    #             data = (_id,) + data
    #             attrs = (conflict_target,) + attrs
                
    #         sql_insert = f"""
    #             INSERT INTO {table_name} ({','.join(attrs)})
    #             VALUES ({','.join(['%s']*len(attrs))})
    #             ON CONFLICT ({conflict_target})
    #             DO UPDATE SET {updates}
    #             RETURNING id;
    #             """
            
    #         self.cursor.execute(sql_insert, data)
    #         returned_id = self.cursor.fetchone()[0]
    #         self.conn.commit()
    #         return returned_id
    #     except Exception as e:
    #         self.conn.rollback()
    #         print(f"❌ Error index {_id}: {e}")
    #         return None
    
    # def upserts(self, table_name:str, datas:tuple, ids:list=[], updates:list=None):
    #     conflict_target = 'id'
    #     update_cols = self.get_columns(table_name)
    #     update_cols.remove(conflict_target)
    #     updates = ','.join([f"{c}={'EXCLUDED.'+c}" for c in update_cols]) if updates is None else updates # Default update all columns except primary key
    #     data_insert = ()
    #     data_upsert = ()
    #     attrs_insert = tuple(update_cols)
    #     attrs_upsert = tuple(update_cols)
    #     for data in datas:
    #         check_ids = [data[update_cols.index(id)].replace("'", "''") for id in ids] 
    #         sql_exists = f"SELECT {conflict_target} FROM {table_name} WHERE {' AND '.join([f'''{id} = '{c_id}'; ''' for id, c_id  in zip(ids, check_ids)])}"
    #         self.cursor.execute(sql_exists)
    #         result = self.cursor.fetchone()
    #         if result:
    #             _id = result[0]
    #             data = (_id,) + data
    #             attrs_upsert = (conflict_target,) + attrs_upsert
    #             data_upsert += (data,)
    #         else:
    #             data_insert += (data,)
        
    #     try:
    #         sql_insert = f"""
    #             INSERT INTO {table_name} ({','.join(attrs_insert)})
    #             VALUES ({','.join(['%s']*len(attrs_insert))})
    #             ON CONFLICT ({conflict_target})
    #             DO UPDATE SET {updates};
    #             """
            
    #         sql_upsert = f"""
    #             INSERT INTO {table_name} ({','.join(attrs_upsert)})
    #             VALUES ({','.join(['%s']*len(attrs_upsert))})
    #             ON CONFLICT ({conflict_target})
    #             DO UPDATE SET {updates};
    #             """
    #         self.cursor.executemany(sql_insert, data_insert)
    #         self.cursor.executemany(sql_upsert, data_upsert)
    #         self.conn.commit()
    #     except Exception as e:
    #         self.conn.rollback()
    #         print(f"❌ Error index {_id}: {e}")

    # def delete(self, table_name, pk_id):
    #     try:
    #         self.cursor.execute(f"DELETE FROM {table_name} WHERE id={pk_id};")
    #         self.conn.commit()
    #     except Exception as e:
    #         self.cursor.execute("ROLLBACK")
    
    # def truncate(self, table_name):
    #     try:
    #         self.cursor.execute(f"TRUNCATE {table_name} CASCADE")
    #         self.conn.commit()
    #     except Exception as e:
    #         self.cursor.execute("ROLLBACK")

    # def query_test(self, sql):
    #     with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
    #         cursor.execute(sql)
    #         return cursor.fetchall()
    # def load(self, table_name):
    #     command = f"SELECT * FROM {table_name} dp WHERE  seg_comment_avg->>'NEG' = '0' AND seg_comment_avg->>'NEU' = '0' AND seg_comment_avg->>'POS' = '0';"
    #     return self.query_test(command)

    # def check_connection(self):
    #     if self.conn is not None and self.conn.closed == 0:
    #         print("Connection is active")
    #         return True
    #     else:
    #         print("Connection is not active")
    #         return False

    # def create_schema(self, sql_path='*.sql'):
    #     with open(sql_path, 'r') as f:
    #         schema = f.read().split('\n\n')
    #     try:
    #         for statement in schema:
    #             self.cursor.execute(statement)
    #             if statement.find('CREATE TABLE') != -1:
    #                 print(f'''📢 Created table {statement.split('"')[1]}''')
    #             if statement.find('ALTER TABLE') != -1:
    #                 alter = statement.split('"')
    #                 print(f'''🔌 Linked table {alter[1]} -> {alter[5]}''')
    #         self.conn.commit()
    #     except Exception as e:
    #         self.cursor.execute("ROLLBACK")
    #         print(f'❌ ROLLBACK: {e}')
    
    # def get_columns(self, table_name):
    #     try:
    #         self.cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = '{table_name}'".format(table_name=table_name))
    #         cols = [i[0] for i in self.cursor.fetchall()]
    #         return cols
    #     except Exception as e:
    #         self.cursor.execute("ROLLBACK")
    #         print(f'❌ ROLLBACK: {e}')
    
    # def get_all_table(self,):
    #     try:
    #         self.cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
    #         tables = [i[0] for i in self.cursor.fetchall()]
    #         return tables
    #     except Exception as e:
    #         self.cursor.execute("ROLLBACK")
    #         print(f'❌ ROLLBACK: {e}')
    
    # def load_mapping(self, table_name, attr):
    #     df = self.query(f"SELECT id, {attr}  FROM {table_name}")
    #     return df.set_index(attr)['id'].to_dict()

