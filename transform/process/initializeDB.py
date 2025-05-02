import os
import psycopg2
from utils import Postgres
from logger import get_logger
logger = get_logger(logs_dir='/var/log/supervisor/initializeDB/', log_filename='initializeDB.log')

with open("rotoro.sql", "r", encoding="utf-8") as f:
    sql_commands = f.read()

def execute_sql_commands(sql_commands):
    db = Postgres()
    if db.is_connected():
        logger.info("Connected to database")
        db.run_sql_file("rotoro.sql")
        db.close()
    else:
        logger.error("Failed to connect to database")
        return
    
def main():
    try:
        execute_sql_commands(sql_commands)
        logger.info("SQL commands executed successfully")
    except Exception as e:
        logger.error(f"Error executing SQL commands: {e}")

if __name__ == "__main__":
    main()