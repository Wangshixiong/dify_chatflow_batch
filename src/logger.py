#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chatflow 自动化测试工具 - 日志和错误处理模块

这个模块提供统一的日志记录和错误处理功能：
1. 自定义异常类
2. 日志配置和管理
3. 错误处理装饰器
4. 性能监控

作者: AI Assistant
创建时间: 2024
"""

import logging
import functools
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional, Dict
import sys


class ChatflowTestError(Exception):
    """
    测试工具基础异常类
    """
    pass


class ConfigurationError(ChatflowTestError):
    """
    配置相关错误
    """
    pass


class ExcelProcessingError(ChatflowTestError):
    """
    Excel 文件处理错误
    """
    pass


class APIConnectionError(ChatflowTestError):
    """
    API 连接错误
    """
    pass


class APIResponseError(ChatflowTestError):
    """
    API 响应错误
    """
    pass


class ConversationError(ChatflowTestError):
    """
    会话管理错误
    """
    pass


class LoggerManager:
    """
    日志管理器
    
    提供统一的日志配置和管理功能
    """
    
    _instance = None
    _loggers = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggerManager, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def setup_logger(
        cls,
        name: str,
        log_file: str = None,
        level: str = 'INFO',
        console_output: bool = True,
        file_output: bool = True,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ) -> logging.Logger:
        """
        设置并获取日志记录器
        
        Args:
            name: 日志记录器名称
            log_file: 日志文件路径
            level: 日志级别
            console_output: 是否输出到控制台
            file_output: 是否输出到文件
            max_file_size: 日志文件最大大小（字节）
            backup_count: 备份文件数量
            
        Returns:
            配置好的日志记录器
        """
        if name in cls._loggers:
            return cls._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        
        # 清除现有的处理器
        logger.handlers.clear()
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台输出
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # 文件输出
        if file_output and log_file:
            # 创建日志目录
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 使用 RotatingFileHandler 进行日志轮转
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        cls._loggers[name] = logger
        return logger
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        获取已配置的日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            日志记录器
        """
        if name not in cls._loggers:
            # 如果没有配置过，使用默认配置
            return cls.setup_logger(name)
        return cls._loggers[name]


def log_execution_time(logger_name: str = 'performance'):
    """
    记录函数执行时间的装饰器
    
    Args:
        logger_name: 日志记录器名称
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = LoggerManager.get_logger(logger_name)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"{func.__name__} 执行完成，耗时: {execution_time:.3f} 秒")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"{func.__name__} 执行失败，耗时: {execution_time:.3f} 秒，错误: {e}")
                raise
        
        return wrapper
    return decorator


def handle_exceptions(logger_name: str = 'error', reraise: bool = True):
    """
    异常处理装饰器
    
    Args:
        logger_name: 日志记录器名称
        reraise: 是否重新抛出异常
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = LoggerManager.get_logger(logger_name)
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 记录详细的错误信息
                error_info = {
                    'function': func.__name__,
                    'args': str(args)[:200] + '...' if len(str(args)) > 200 else str(args),
                    'kwargs': str(kwargs)[:200] + '...' if len(str(kwargs)) > 200 else str(kwargs),
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'traceback': traceback.format_exc()
                }
                
                logger.error(f"函数 {func.__name__} 发生异常: {error_info}")
                
                if reraise:
                    raise
                else:
                    return None
        
        return wrapper
    return decorator


def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    logger_name: str = 'retry'
):
    """
    失败重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff_factor: 延迟时间递增因子
        exceptions: 需要重试的异常类型
        logger_name: 日志记录器名称
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = LoggerManager.get_logger(logger_name)
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        logger.error(f"{func.__name__} 重试 {max_retries} 次后仍然失败: {e}")
                        raise
                    
                    wait_time = delay * (backoff_factor ** attempt)
                    logger.warning(f"{func.__name__} 第 {attempt + 1} 次尝试失败: {e}，{wait_time:.1f} 秒后重试")
                    time.sleep(wait_time)
        
        return wrapper
    return decorator


class PerformanceMonitor:
    """
    性能监控器
    
    用于监控和记录系统性能指标
    """
    
    def __init__(self, logger_name: str = 'performance'):
        self.logger = LoggerManager.get_logger(logger_name)
        self.metrics = {}
        self.start_times = {}
    
    def start_timer(self, name: str) -> None:
        """
        开始计时
        
        Args:
            name: 计时器名称
        """
        self.start_times[name] = time.time()
        self.logger.debug(f"开始计时: {name}")
    
    def end_timer(self, name: str) -> float:
        """
        结束计时并返回耗时
        
        Args:
            name: 计时器名称
            
        Returns:
            耗时（秒）
        """
        if name not in self.start_times:
            self.logger.warning(f"计时器 {name} 未启动")
            return 0.0
        
        elapsed_time = time.time() - self.start_times[name]
        del self.start_times[name]
        
        # 记录到指标中
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(elapsed_time)
        
        self.logger.info(f"计时结束: {name}，耗时: {elapsed_time:.3f} 秒")
        return elapsed_time
    
    def get_average_time(self, name: str) -> float:
        """
        获取平均耗时
        
        Args:
            name: 计时器名称
            
        Returns:
            平均耗时（秒）
        """
        if name not in self.metrics or not self.metrics[name]:
            return 0.0
        
        return sum(self.metrics[name]) / len(self.metrics[name])
    
    def get_total_time(self, name: str) -> float:
        """
        获取总耗时
        
        Args:
            name: 计时器名称
            
        Returns:
            总耗时（秒）
        """
        if name not in self.metrics:
            return 0.0
        
        return sum(self.metrics[name])
    
    def get_stats(self, name: str) -> Dict[str, Any]:
        """
        获取统计信息
        
        Args:
            name: 计时器名称
            
        Returns:
            统计信息字典
        """
        if name not in self.metrics or not self.metrics[name]:
            return {'count': 0, 'total': 0.0, 'average': 0.0, 'min': 0.0, 'max': 0.0}
        
        times = self.metrics[name]
        return {
            'count': len(times),
            'total': sum(times),
            'average': sum(times) / len(times),
            'min': min(times),
            'max': max(times)
        }
    
    def print_summary(self) -> None:
        """
        打印性能总结
        """
        print("\n" + "="*50)
        print("性能监控总结")
        print("="*50)
        
        for name in self.metrics:
            stats = self.get_stats(name)
            print(f"{name}:")
            print(f"  调用次数: {stats['count']}")
            print(f"  总耗时: {stats['total']:.3f} 秒")
            print(f"  平均耗时: {stats['average']:.3f} 秒")
            print(f"  最短耗时: {stats['min']:.3f} 秒")
            print(f"  最长耗时: {stats['max']:.3f} 秒")
            print()
        
        print("="*50)


def setup_global_exception_handler(logger_name: str = 'global_error'):
    """
    设置全局异常处理器
    
    Args:
        logger_name: 日志记录器名称
    """
    logger = LoggerManager.get_logger(logger_name)
    
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            # 允许 Ctrl+C 正常退出
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger.critical(
            "未捕获的异常",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
    
    sys.excepthook = handle_exception


# 测试代码
if __name__ == '__main__':
    # 设置日志
    logger = LoggerManager.setup_logger(
        'test',
        log_file='logs/test.log',
        level='DEBUG'
    )
    
    # 设置全局异常处理
    setup_global_exception_handler()
    
    # 创建性能监控器
    monitor = PerformanceMonitor()
    
    # 测试装饰器
    @log_execution_time('test')
    @handle_exceptions('test')
    @retry_on_failure(max_retries=2, delay=0.1)
    def test_function(should_fail: bool = False):
        monitor.start_timer('test_function')
        time.sleep(0.1)  # 模拟工作
        
        if should_fail:
            raise ValueError("测试异常")
        
        monitor.end_timer('test_function')
        return "成功"
    
    # 测试成功情况
    logger.info("测试成功情况")
    result = test_function(False)
    logger.info(f"结果: {result}")
    
    # 测试失败情况
    logger.info("测试失败情况")
    try:
        test_function(True)
    except ValueError as e:
        logger.info(f"捕获到预期异常: {e}")
    
    # 打印性能总结
    monitor.print_summary()
    
    logger.info("测试完成")