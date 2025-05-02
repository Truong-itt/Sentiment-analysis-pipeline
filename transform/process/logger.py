import logging
import os
import sys
from datetime import datetime
import pytz

def get_logger(
        logs_dir: str = '/var/log/supervisor/',
        log_filename: str = None, 
        log_format: str = '%(asctime)s @%(name)s [%(levelname)s]:    %(message)s'
    ) -> logging.Logger:
    """ 
    Trả về một đối tượng Logger để ghi log vào thư mục logs_dir.

    Args:
        logs_dir (str, optional): Thư mục nơi lưu trữ các log.
        log_filename (str, optional): Tên file log cụ thể. Nếu không truyền, sẽ dùng tên script.
        log_format (str, optional): Định dạng log.

    Returns:
        logging.Logger: Đối tượng Logger để ghi log từ chương trình.
    """
    if log_filename is None:
        script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        log_filename = f"{script_name}.log"

    logs_path = os.path.join(logs_dir, log_filename)
    os.makedirs(os.path.dirname(logs_path), exist_ok=True)
    logger = logging.getLogger(log_filename)
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    fh = logging.FileHandler(logs_path, mode='a', encoding='utf-8')
    fh.setLevel(logging.INFO)

    class HCMFormatter(logging.Formatter):
        def __init__(self, fmt=None, datefmt=None, style='%'):
            super().__init__(fmt, datefmt, style)
            self.zone = pytz.timezone("Asia/Ho_Chi_Minh")

        def formatTime(self, record, datefmt=None):
            dt = datetime.fromtimestamp(record.created, self.zone)
            if datefmt:
                return dt.strftime(datefmt)
            else:
                return dt.isoformat()

    formatter = HCMFormatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
    fh.setFormatter(formatter)

    logger.addHandler(fh)
    logger.propagate = False
    return logger
