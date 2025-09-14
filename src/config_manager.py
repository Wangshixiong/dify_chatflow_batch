#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
负责读取和验证config.ini配置文件
"""

import configparser
import os
import sys
from pathlib import Path
from typing import Dict, Any


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.ini"):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self._load_config()
    
    def _load_config(self) -> None:
        """
        加载配置文件
        
        Raises:
            FileNotFoundError: 配置文件不存在
            configparser.Error: 配置文件格式错误
        """
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(
                f"配置文件 {self.config_file} 不存在。\n"
                f"请复制 examples/config.ini.template 为 {self.config_file} 并填入正确的配置信息。"
            )
        
        try:
            self.config.read(self.config_file, encoding='utf-8')
        except configparser.Error as e:
            raise configparser.Error(f"配置文件格式错误: {e}")
        
        # 验证配置
        self._validate_config()
    
    def _validate_config(self) -> None:
        """
        验证配置文件的必要字段
        
        Raises:
            ValueError: 配置验证失败
        """
        required_sections = ['API']
        required_fields = {
            'API': ['API_URL', 'API_KEY', 'USER_ID']
        }
        
        # 检查必要的section
        for section in required_sections:
            if not self.config.has_section(section):
                raise ValueError(f"配置文件缺少必要的section: [{section}]")
        
        # 检查必要的字段
        for section, fields in required_fields.items():
            for field in fields:
                if not self.config.has_option(section, field):
                    raise ValueError(f"配置文件缺少必要的字段: [{section}] {field}")
                
                value = self.config.get(section, field).strip()
                if not value:
                    raise ValueError(f"配置字段不能为空: [{section}] {field}")
        
        # 验证API_URL格式
        api_url = self.get_api_url()
        if not (api_url.startswith('http://') or api_url.startswith('https://')):
            raise ValueError("API_URL必须以http://或https://开头")
        
        # 验证超时时间
        timeout = self.get_timeout()
        if timeout <= 0:
            raise ValueError("TIMEOUT必须大于0")
    
    def get_api_url(self) -> str:
        """获取API URL"""
        return self.config.get('API', 'API_URL').strip().rstrip('/')
    
    def get_api_key(self) -> str:
        """获取API密钥"""
        return self.config.get('API', 'API_KEY').strip()
    
    def get_user_id(self) -> str:
        """获取用户ID"""
        return self.config.get('API', 'USER_ID').strip()
    
    def get_timeout(self) -> int:
        """获取超时时间"""
        return self.config.getint('API', 'TIMEOUT', fallback=30)
    
    def get_response_mode(self) -> str:
        """获取响应模式"""
        mode = self.config.get('API', 'RESPONSE_MODE', fallback='streaming').strip().lower()
        if mode not in ['blocking', 'streaming']:
            raise ValueError("RESPONSE_MODE必须是'blocking'或'streaming'")
        return mode
    
    def get_log_level(self) -> str:
        """获取日志级别"""
        try:
            return self.config.get('LOGGING', 'LOG_LEVEL').strip().upper()
        except configparser.NoOptionError:
            return 'INFO'  # 默认INFO级别
    
    def get_log_file(self) -> str:
        """获取日志文件路径"""
        try:
            log_file = self.config.get('LOGGING', 'LOG_FILE').strip()
            return log_file if log_file else None
        except configparser.NoOptionError:
            return None
    
    def get_output_dir(self) -> str:
        """获取输出目录"""
        try:
            output_dir = self.config.get('OUTPUT', 'OUTPUT_DIR').strip()
            if output_dir:
                # 确保目录存在
                Path(output_dir).mkdir(parents=True, exist_ok=True)
                return output_dir
            return '.'  # 默认当前目录
        except configparser.NoOptionError:
            return '.'
    
    def get_include_timestamp(self) -> bool:
        """是否在文件名中包含时间戳"""
        try:
            return self.config.getboolean('OUTPUT', 'INCLUDE_TIMESTAMP')
        except (configparser.NoOptionError, ValueError):
            return True  # 默认包含时间戳
    
    def get_log_config(self) -> Dict[str, str]:
        """获取日志配置"""
        log_file = self.get_log_file()
        if not log_file:
            # 如果没有配置日志文件，使用默认路径
            log_file = "logs/chatflow_test.log"
        
        return {
            'level': self.get_log_level(),
            'file': log_file
        }
    
    def get_api_config(self) -> Dict[str, Any]:
        """获取API配置"""
        return {
            'url': self.get_api_url(),
            'key': self.get_api_key(),
            'user_id': self.get_user_id(),
            'timeout': self.get_timeout()
        }
    
    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置信息（用于调试）"""
        config_dict = {}
        for section_name in self.config.sections():
            config_dict[section_name] = dict(self.config.items(section_name))
        
        # 脱敏处理API密钥
        if 'API' in config_dict and 'api_key' in config_dict['API']:
            api_key = config_dict['API']['api_key']
            if len(api_key) > 8:
                config_dict['API']['api_key'] = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:]
        
        return config_dict


if __name__ == "__main__":
    # 测试配置管理器
    try:
        config_manager = ConfigManager()
        print("配置加载成功！")
        print(f"API URL: {config_manager.get_api_url()}")
        print(f"用户ID: {config_manager.get_user_id()}")
        print(f"超时时间: {config_manager.get_timeout()}秒")
        print(f"日志级别: {config_manager.get_log_level()}")
        print(f"输出目录: {config_manager.get_output_dir()}")
        print(f"包含时间戳: {config_manager.get_include_timestamp()}")
    except Exception as e:
        print(f"配置加载失败: {e}")
        sys.exit(1)