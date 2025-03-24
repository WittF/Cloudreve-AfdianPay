import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger():
    # 创建logs目录（如果不存在）
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 配置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 创建文件处理器（限制大小为5MB，最多保留3个备份）
    file_handler = RotatingFileHandler(
        'logs/cloudreve_pay.log',
        maxBytes=5*1024*1024,
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 创建日志记录器
    logger = logging.getLogger('CloudrevePay')
    logger.setLevel(logging.INFO)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 创建全局日志记录器实例
logger = setup_logger() 