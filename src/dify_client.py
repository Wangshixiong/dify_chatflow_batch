#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify API调用模块
负责与Dify Chatflow API进行通信
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import logging


class DifyAPIError(Exception):
    """Dify API调用异常"""
    pass


class DifyClient:
    """Dify API客户端"""
    
    def __init__(self, api_url: str, api_key: str, timeout: int = 30, response_mode: str = "blocking"):
        """
        初始化Dify客户端
        
        Args:
            api_url: API基础URL
            api_key: API密钥
            timeout: 请求超时时间（秒）
            response_mode: 响应模式（blocking或streaming）
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.response_mode = response_mode
        self.session = requests.Session()
        
        # 设置默认请求头
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'Chatflow-Test-Tool/1.0.0'
        })
        
        self.logger = logging.getLogger(__name__)
    
    def send_chat_message(self, 
                         query: str, 
                         user_id: str,
                         conversation_id: Optional[str] = None,
                         inputs: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], float]:
        """
        发送聊天消息到Dify Chatflow
        
        Args:
            query: 用户问题
            user_id: 用户ID
            conversation_id: 会话ID（可选，新对话时不传）
            inputs: 额外输入参数（可选）

            
        Returns:
            (API响应数据, 响应时间)
            
        Raises:
            DifyAPIError: API调用失败
        """
        url = f"{self.api_url}/chat-messages"
        
        # 构建请求体
        payload = {
            "inputs": inputs or {},
            "query": query,
            "response_mode": self.response_mode,
            "user": user_id
        }
        
        # 如果有会话ID，添加到请求中
        if conversation_id:
            payload["conversation_id"] = conversation_id
        
        self.logger.debug(f"发送API请求: {url}")
        self.logger.debug(f"请求体: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        start_time = time.time()
        
        try:
            # 根据响应模式选择不同的处理方式
            if self.response_mode == "streaming":
                return self._handle_streaming_response(url, payload, start_time)
            else:
                return self._handle_blocking_response(url, payload, start_time)
            
        except requests.exceptions.Timeout:
            raise DifyAPIError(f"API请求超时（{self.timeout}秒）")
        except requests.exceptions.ConnectionError:
            raise DifyAPIError("API连接失败，请检查网络连接和API地址")
        except requests.exceptions.RequestException as e:
            raise DifyAPIError(f"API请求异常: {e}")
    
    def _handle_blocking_response(self, url: str, payload: Dict[str, Any], start_time: float) -> Tuple[Dict[str, Any], float]:
        """
        处理阻塞模式的响应
        """
        response = self.session.post(
            url,
            json=payload,
            timeout=self.timeout
        )
        
        response_time = time.time() - start_time
        
        self.logger.debug(f"API响应状态码: {response.status_code}")
        self.logger.debug(f"API响应时间: {response_time:.2f}秒")
        
        # 检查HTTP状态码
        if response.status_code != 200:
            error_msg = f"API请求失败，状态码: {response.status_code}"
            try:
                error_data = response.json()
                if 'message' in error_data:
                    error_msg += f"，错误信息: {error_data['message']}"
            except:
                error_msg += f"，响应内容: {response.text[:200]}"
            
            raise DifyAPIError(error_msg)
        
        # 解析响应JSON
        try:
            response_data = response.json()
        except json.JSONDecodeError as e:
            raise DifyAPIError(f"API响应JSON解析失败: {e}")
        
        self.logger.debug(f"API响应数据: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        
        # 验证响应格式
        self._validate_response(response_data)
        
        return response_data, response_time
    
    def _handle_streaming_response(self, url: str, payload: Dict[str, Any], start_time: float) -> Tuple[Dict[str, Any], float]:
        """
        处理流式响应
        """
        # 设置流式请求的headers
        headers = self.session.headers.copy()
        headers['Accept'] = 'text/event-stream'
        
        response = self.session.post(
            url,
            json=payload,
            timeout=self.timeout,
            stream=True,
            headers=headers
        )
        
        self.logger.debug(f"流式API响应状态码: {response.status_code}")
        
        # 检查HTTP状态码
        if response.status_code != 200:
            error_msg = f"API请求失败，状态码: {response.status_code}"
            try:
                error_data = response.json()
                if 'message' in error_data:
                    error_msg += f"，错误信息: {error_data['message']}"
            except:
                error_msg += f"，响应内容: {response.text[:200]}"
            
            raise DifyAPIError(error_msg)
        
        # 解析流式响应
        full_answer = ""
        conversation_id = None
        message_id = None
        
        try:
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith('data: '):
                    try:
                        # 移除'data: '前缀并解析JSON
                        json_str = line[6:].strip()
                        if json_str:
                            event_data = json.loads(json_str)
                            
                            # 处理不同类型的事件
                            event_type = event_data.get('event', '')
                            
                            if event_type == 'message':
                                # 累积答案内容
                                answer_chunk = event_data.get('answer', '')
                                full_answer += answer_chunk
                                
                                # 获取会话ID和消息ID
                                if not conversation_id:
                                    conversation_id = event_data.get('conversation_id')
                                if not message_id:
                                    message_id = event_data.get('message_id')
                            
                            elif event_type == 'message_end':
                                # 消息结束，可以获取最终的元数据
                                if not conversation_id:
                                    conversation_id = event_data.get('conversation_id')
                                if not message_id:
                                    message_id = event_data.get('id')
                                break
                            
                            elif event_type == 'error':
                                error_msg = event_data.get('message', '未知错误')
                                raise DifyAPIError(f"流式响应错误: {error_msg}")
                    
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"解析流式响应行失败: {line}, 错误: {e}")
                        continue
        
        except Exception as e:
            raise DifyAPIError(f"处理流式响应失败: {e}")
        
        response_time = time.time() - start_time
        self.logger.debug(f"流式API响应时间: {response_time:.2f}秒")
        
        # 构建标准格式的响应数据
        response_data = {
            'answer': full_answer,
            'conversation_id': conversation_id,
            'message_id': message_id
        }
        
        self.logger.debug(f"流式响应合并结果: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        
        return response_data, response_time
    
    def _validate_response(self, response_data: Dict[str, Any]) -> None:
        """
        验证API响应格式
        
        Args:
            response_data: API响应数据
            
        Raises:
            DifyAPIError: 响应格式不正确
        """
        # 检查是否有错误信息
        if 'error' in response_data:
            error_msg = response_data.get('message', '未知错误')
            raise DifyAPIError(f"API返回错误: {error_msg}")
        
        # 检查必要字段
        required_fields = ['answer', 'conversation_id']
        missing_fields = []
        
        for field in required_fields:
            if field not in response_data:
                missing_fields.append(field)
        
        if missing_fields:
            self.logger.warning(f"API响应缺少字段: {missing_fields}")
            # 不抛出异常，只记录警告，因为某些情况下可能确实没有这些字段
    
    def extract_answer(self, response_data: Dict[str, Any]) -> str:
        """
        从API响应中提取答案
        
        Args:
            response_data: API响应数据
            
        Returns:
            提取的答案文本
        """
        # 优先从answer字段获取
        if 'answer' in response_data:
            return str(response_data['answer']).strip()
        
        # 如果没有answer字段，尝试从其他可能的字段获取
        possible_fields = ['message', 'content', 'text', 'response']
        for field in possible_fields:
            if field in response_data and response_data[field]:
                self.logger.warning(f"从'{field}'字段获取答案，而非标准的'answer'字段")
                return str(response_data[field]).strip()
        
        # 如果都没有，返回空字符串
        self.logger.warning("API响应中未找到答案内容")
        return ""
    
    def extract_conversation_id(self, response_data: Dict[str, Any]) -> Optional[str]:
        """
        从API响应中提取会话ID
        
        Args:
            response_data: API响应数据
            
        Returns:
            会话ID，如果没有则返回None
        """
        conversation_id = response_data.get('conversation_id')
        if conversation_id:
            return str(conversation_id).strip()
        return None
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        测试API连接
        
        Returns:
            (是否连接成功, 结果信息)
        """
        try:
            # 发送一个简单的测试消息
            response_data, response_time = self.send_chat_message(
                query="测试连接",
                user_id="test_user"
            )
            
            return True, f"连接成功，响应时间: {response_time:.2f}秒"
            
        except DifyAPIError as e:
            return False, f"连接失败: {e}"
        except Exception as e:
            return False, f"连接异常: {e}"
    
    def get_api_info(self) -> Dict[str, Any]:
        """
        获取API客户端信息
        
        Returns:
            API客户端配置信息
        """
        # 脱敏处理API密钥
        masked_api_key = self.api_key[:4] + '*' * (len(self.api_key) - 8) + self.api_key[-4:] if len(self.api_key) > 8 else '*' * len(self.api_key)
        
        return {
            'api_url': self.api_url,
            'api_key': masked_api_key,
            'timeout': self.timeout,
            'user_agent': self.session.headers.get('User-Agent', '')
        }


if __name__ == "__main__":
    # 测试Dify客户端
    import sys
    
    # 这里需要真实的API配置才能测试
    # 示例配置（请替换为真实值）
    test_config = {
        'api_url': 'http://localhost/v1',
        'api_key': 'your_api_key_here',
        'user_id': 'test_user'
    }
    
    print("Dify客户端测试")
    print("注意: 需要真实的API配置才能进行连接测试")
    
    try:
        client = DifyClient(
            api_url=test_config['api_url'],
            api_key=test_config['api_key']
        )
        
        print(f"客户端信息: {client.get_api_info()}")
        
        # 如果有真实配置，可以取消注释进行连接测试
        # success, message = client.test_connection()
        # print(f"连接测试: {message}")
        
    except Exception as e:
        print(f"客户端初始化失败: {e}")
        sys.exit(1)