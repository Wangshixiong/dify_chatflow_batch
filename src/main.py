#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chatflow 自动化测试工具 - 主程序

这个模块是整个工具的入口点，负责：n1. 命令行参数解析
2. 配置文件加载
3. 协调各个模块的工作
4. 进度显示和用户交互
5. 错误处理和日志记录

作者: AI Assistant
创建时间: 2024
"""

import argparse
import sys
import os
import time
from datetime import datetime
from pathlib import Path
import logging
from typing import Optional, List, Dict, Any

# 添加当前目录到Python路径，以便导入其他模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_manager import ConfigManager
from excel_handler import ExcelHandler
from dify_client import DifyClient
from conversation_manager import ConversationManager


class ChatflowTestTool:
    """
    Chatflow 自动化测试工具主类
    
    这个类协调所有组件，执行完整的测试流程：
    1. 读取测试用例
    2. 调用 Dify API
    3. 管理会话状态
    4. 保存测试结果
    """
    
    def __init__(self, config_path: str = "config.ini"):
        """
        初始化测试工具
        
        Args:
            config_path: 配置文件路径
        """
        self.config_manager = ConfigManager(config_path)
        self.excel_handler = ExcelHandler()
        self.conversation_manager = ConversationManager()
        self.dify_client = None
        self.logger = None
        
        # 统计信息
        self.stats = {
            'total_cases': 0,
            'processed_cases': 0,
            'successful_cases': 0,
            'failed_cases': 0,
            'start_time': None,
            'end_time': None
        }
    
    def setup_logging(self) -> None:
        """
        设置日志记录
        """
        log_config = self.config_manager.get_log_config()
        
        # 创建日志目录
        log_file = Path(log_config['file'])
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 配置日志格式
        logging.basicConfig(
            level=getattr(logging, log_config['level'].upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger('ChatflowTestTool')
        self.logger.info("日志系统初始化完成")
    
    def initialize_dify_client(self) -> bool:
        """
        初始化 Dify 客户端
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            api_config = self.config_manager.get_api_config()
            response_mode = self.config_manager.get_response_mode()
            self.dify_client = DifyClient(
                api_url=api_config['url'],
                api_key=api_config['key'],
                timeout=api_config['timeout'],
                response_mode=response_mode
            )
            
            # 测试连接
            if self.dify_client.test_connection():
                self.logger.info("Dify API 连接测试成功")
                return True
            else:
                self.logger.error("Dify API 连接测试失败")
                return False
                
        except Exception as e:
            self.logger.error(f"初始化 Dify 客户端失败: {e}")
            return False
    
    def load_test_cases(self, input_file: str) -> Optional[List[Dict[str, Any]]]:
        """
        加载测试用例
        
        Args:
            input_file: 输入文件路径
            
        Returns:
            测试用例列表，失败时返回 None
        """
        try:
            self.logger.info(f"开始加载测试用例: {input_file}")
            test_cases = self.excel_handler.read_test_cases(input_file)
            
            # 验证测试用例结构
            validation_result = self.excel_handler.validate_test_case_structure(test_cases)
            if not validation_result['valid']:
                self.logger.error(f"测试用例验证失败: {validation_result['errors']}")
                return None
            
            self.stats['total_cases'] = len(test_cases)
            self.logger.info(f"成功加载 {len(test_cases)} 个测试用例")
            return test_cases
            
        except Exception as e:
            self.logger.error(f"加载测试用例失败: {e}")
            return None
    
    def process_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理单个测试用例
        
        Args:
            test_case: 测试用例数据
            
        Returns:
            处理结果
        """
        result = {
            'conversation_id': test_case.get('conversation_group_id', ''),
            'turn_number': test_case.get('turn_number', 1),
            'user_question': test_case.get('user_question', ''),
            'expected_reply': test_case.get('expected_reply', ''),
            'chatflow_reply': '',
            'response_time': 0,
            'api_status': 'failed',
            'error_details': '',
            'call_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            # 获取或创建会话ID
            conversation_id = self.conversation_manager.get_conversation_id(
                test_case.get('conversation_group_id', '')
            )
            
            # 准备API调用参数
            user_id = self.config_manager.get_api_config().get('user_id', 'test_user')
            
            # 记录开始时间
            start_time = time.time()
            
            # 调用 Dify API（带重试机制）
            max_retries = 3
            retry_delay = 5  # 秒
            api_response = None
            response_time = 0
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    api_response, response_time = self.dify_client.send_chat_message(
                        query=test_case['user_question'],
                        user_id=user_id,
                        conversation_id=conversation_id if conversation_id != 'new' else None,
                        inputs=test_case.get('inputs', {})
                    )
                    break  # 成功则跳出重试循环
                    
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        self.logger.warning(f"API调用失败，等待{retry_delay}秒后重试... (尝试 {attempt + 1}/{max_retries})，错误: {str(e)}")
                        time.sleep(retry_delay)
                    else:
                        # 最后一次尝试失败，抛出异常
                        raise last_error
            
            # 记录响应时间
            result['response_time'] = round(response_time, 3)
            
            if api_response:
                # 提取答案
                chatflow_reply = self.dify_client.extract_answer(api_response)
                result['chatflow_reply'] = chatflow_reply
                
                # 更新会话ID
                new_conversation_id = self.dify_client.extract_conversation_id(api_response)
                if new_conversation_id:
                    self.conversation_manager.set_conversation_id(
                        test_case.get('conversation_group_id', ''),
                        new_conversation_id
                    )
                
                result['api_status'] = '成功'
                self.stats['successful_cases'] += 1
                
            else:
                result['error_details'] = '未收到有效的API响应'
                self.stats['failed_cases'] += 1
                
        except Exception as e:
            result['error_details'] = str(e)
            self.stats['failed_cases'] += 1
            self.logger.error(f"处理测试用例失败: {e}")
        
        self.stats['processed_cases'] += 1
        return result
    
    def show_progress(self, current: int, total: int, test_case: Dict[str, Any]) -> None:
        """
        显示进度信息
        
        Args:
            current: 当前处理的用例编号
            total: 总用例数
            test_case: 当前测试用例
        """
        percentage = (current / total) * 100
        conversation_id = test_case.get('conversation_group_id', 'N/A')
        turn_num = test_case.get('turn_number', 'N/A')
        question_preview = test_case.get('user_question', '')[:50] + '...' if len(test_case.get('user_question', '')) > 50 else test_case.get('user_question', '')
        
        print(f"\r进度: {current}/{total} ({percentage:.1f}%) | 对话ID: {conversation_id} | 轮次: {turn_num} | 问题: {question_preview}", end='', flush=True)
    
    def save_results(self, results: List[Dict[str, Any]], output_file: str) -> bool:
        """
        保存测试结果
        
        Args:
            results: 测试结果列表
            output_file: 输出文件路径
            
        Returns:
            bool: 保存是否成功
        """
        try:
            output_dir = self.config_manager.get_output_dir()
            include_timestamp = self.config_manager.get_include_timestamp()
            
            result_file = self.excel_handler.create_result_file(
                results,
                output_dir=output_dir,
                include_timestamp=include_timestamp
            )
            success = result_file is not None
            
            if success:
                self.logger.info(f"测试结果已保存到: {result_file}")
                return True
            else:
                self.logger.error("保存测试结果失败")
                return False
                
        except Exception as e:
            self.logger.error(f"保存测试结果时发生错误: {e}")
            return False
    
    def print_summary(self) -> None:
        """
        打印测试总结
        """
        print("\n" + "="*60)
        print("测试完成总结")
        print("="*60)
        print(f"总用例数: {self.stats['total_cases']}")
        print(f"已处理: {self.stats['processed_cases']}")
        print(f"成功: {self.stats['successful_cases']}")
        print(f"失败: {self.stats['failed_cases']}")
        
        if self.stats['total_cases'] > 0:
            success_rate = (self.stats['successful_cases'] / self.stats['total_cases']) * 100
            print(f"成功率: {success_rate:.1f}%")
        
        if self.stats['start_time'] and self.stats['end_time']:
            duration = self.stats['end_time'] - self.stats['start_time']
            print(f"总耗时: {duration:.2f} 秒")
        
        # 显示会话统计
        conv_stats = self.conversation_manager.get_statistics()
        print(f"管理的对话数: {conv_stats['total_conversations']}")
        print(f"总轮次数: {conv_stats['total_turns']}")
        print("="*60)
    
    def run(self, input_file: str, output_file: str = None) -> bool:
        """
        运行测试工具
        
        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径（可选）
            
        Returns:
            bool: 运行是否成功
        """
        try:
            # 记录开始时间
            self.stats['start_time'] = time.time()
            
            # 设置日志
            self.setup_logging()
            
            # 初始化 Dify 客户端
            if not self.initialize_dify_client():
                return False
            
            # 加载测试用例
            test_cases = self.load_test_cases(input_file)
            if not test_cases:
                return False
            
            # 处理测试用例
            results = []
            print(f"\n开始处理 {len(test_cases)} 个测试用例...")
            
            # 准备输出文件路径
            if not output_file:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"result_{timestamp}.xlsx"
            
            output_dir = self.config_manager.get_output_dir()
            full_output_path = os.path.join(output_dir, output_file)
            
            for i, test_case in enumerate(test_cases, 1):
                self.show_progress(i, len(test_cases), test_case)
                result = self.process_test_case(test_case)
                results.append(result)
                
                # 实时写入Excel文件
                try:
                    self.excel_handler.append_result_to_file(result, full_output_path)
                except Exception as e:
                    self.logger.error(f"实时写入结果失败: {e}")
                
                # 在测试用例之间添加适当延迟，避免过快请求导致工作流冲突
                if i < len(test_cases) - 1:  # 不是最后一个用例
                    time.sleep(2)  # 等待2秒
            
            print()  # 换行
            
            # 检查是否有备份保存需求（如果实时写入失败）
            if os.path.exists(full_output_path):
                self.logger.info(f"测试结果已实时保存到: {full_output_path}")
                success = True
            else:
                # 如果实时写入失败，尝试批量保存作为备份
                self.logger.warning("实时写入失败，尝试批量保存作为备份")
                success = self.save_results(results, output_file)
            
            if success:
                # 记录结束时间
                self.stats['end_time'] = time.time()
                
                # 打印总结
                self.print_summary()
                
                return True
            else:
                return False
                
        except KeyboardInterrupt:
            print("\n\n用户中断了测试过程")
            self.logger.info("用户中断了测试过程")
            return False
        except Exception as e:
            self.logger.error(f"运行测试工具时发生错误: {e}")
            print(f"\n错误: {e}")
            return False


def create_argument_parser() -> argparse.ArgumentParser:
    """
    创建命令行参数解析器
    
    Returns:
        配置好的参数解析器
    """
    parser = argparse.ArgumentParser(
        description='Chatflow 自动化测试工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py test_cases.xlsx                    # 使用默认配置和输出文件名
  python main.py test_cases.xlsx -o results.xlsx   # 指定输出文件名
  python main.py test_cases.xlsx -c my_config.ini  # 使用自定义配置文件
  python main.py --help                            # 显示帮助信息

配置文件:
  工具需要一个配置文件（默认为 config.ini）来设置 API 参数。
  请参考 config.ini.template 创建您的配置文件。
        """
    )
    
    parser.add_argument(
        'input_file',
        help='输入的测试用例 Excel 文件路径'
    )
    
    parser.add_argument(
        '-o', '--output',
        dest='output_file',
        help='输出的结果 Excel 文件路径（可选，默认自动生成）'
    )
    
    parser.add_argument(
        '-c', '--config',
        dest='config_file',
        default='config.ini',
        help='配置文件路径（默认: config.ini）'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Chatflow 自动化测试工具 v1.0.0'
    )
    
    return parser


def main():
    """
    主函数
    """
    # 解析命令行参数
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # 检查输入文件是否存在
    if not os.path.exists(args.input_file):
        print(f"错误: 输入文件不存在: {args.input_file}")
        sys.exit(1)
    
    # 检查配置文件是否存在
    if not os.path.exists(args.config_file):
        print(f"错误: 配置文件不存在: {args.config_file}")
        print("请参考 config.ini.template 创建配置文件")
        sys.exit(1)
    
    # 创建并运行测试工具
    tool = ChatflowTestTool(args.config_file)
    
    print("Chatflow 自动化测试工具 v1.0.0")
    print(f"输入文件: {args.input_file}")
    print(f"配置文件: {args.config_file}")
    if args.output_file:
        print(f"输出文件: {args.output_file}")
    print("-" * 50)
    
    # 运行测试
    success = tool.run(args.input_file, args.output_file)
    
    if success:
        print("\n测试完成！")
        sys.exit(0)
    else:
        print("\n测试失败！")
        sys.exit(1)


if __name__ == '__main__':
    main()