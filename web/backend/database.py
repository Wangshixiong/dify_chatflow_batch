"""
数据库管理模块
使用SQLite存储配置、测试历史等数据
"""
import os
import sqlite3
from typing import Optional, Dict, Any
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 默认数据库路径
            self.db_path = Path(__file__).parent.parent / "data" / "app.db"
        else:
            self.db_path = Path(db_path)
        
        # 确保数据目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库
        self.init_database()
    
    def init_database(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 配置表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS configs (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    api_url TEXT NOT NULL,
                    api_key_encrypted TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    timeout INTEGER NOT NULL DEFAULT 120,
                    response_mode TEXT NOT NULL DEFAULT 'streaming',
                    log_level TEXT NOT NULL DEFAULT 'INFO',
                    output_dir TEXT,
                    include_timestamp BOOLEAN NOT NULL DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN NOT NULL DEFAULT 0
                )
            ''')
            
            # 测试用例表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_cases (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    round INTEGER NOT NULL,
                    user_question TEXT NOT NULL,
                    expected_response TEXT,
                    inputs TEXT,  -- JSON字符串
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 测试任务表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_tasks (
                    id TEXT PRIMARY KEY,
                    config_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'preparing',
                    total_cases INTEGER NOT NULL DEFAULT 0,
                    completed_cases INTEGER NOT NULL DEFAULT 0,
                    success_cases INTEGER NOT NULL DEFAULT 0,
                    failed_cases INTEGER NOT NULL DEFAULT 0,
                    current_case_id TEXT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (config_id) REFERENCES configs (id)
                )
            ''')
            
            # 测试结果表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_results (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    case_id TEXT NOT NULL,
                    status TEXT NOT NULL,  -- success, failed, skipped
                    response TEXT,
                    response_time REAL,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES test_tasks (id),
                    FOREIGN KEY (case_id) REFERENCES test_cases (id)
                )
            ''')
            
            # 系统设置表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info(f"数据库初始化完成: {self.db_path}")
    
    def execute_query(self, query: str, params: tuple = None) -> list:
        """执行查询并返回结果"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row  # 返回字典格式
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """执行更新操作并返回影响的行数"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.rowcount
    
    def get_setting(self, key: str) -> Optional[str]:
        """获取系统设置"""
        result = self.execute_query(
            "SELECT value FROM system_settings WHERE key = ?", (key,)
        )
        return result[0]['value'] if result else None
    
    def set_setting(self, key: str, value: str):
        """设置系统设置"""
        self.execute_update(
            """INSERT OR REPLACE INTO system_settings (key, value, updated_at) 
               VALUES (?, ?, CURRENT_TIMESTAMP)""",
            (key, value)
        )

# 全局数据库实例
db = DatabaseManager()