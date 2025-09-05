#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话管理模块
负责跟踪和管理多轮对话的conversation_id
"""

from typing import Dict, Optional, List, Any
import logging
from datetime import datetime


class ConversationManager:
    """会话管理器"""
    
    def __init__(self):
        """
        初始化会话管理器
        """
        # 存储对话组ID到conversation_id的映射
        self._conversation_mapping: Dict[str, str] = {}
        
        # 存储每个对话组的轮次信息
        self._conversation_turns: Dict[str, List[Dict[str, Any]]] = {}
        
        # 存储会话创建时间
        self._conversation_created_time: Dict[str, str] = {}
        
        self.logger = logging.getLogger(__name__)
    
    def get_conversation_id(self, conversation_group_id: str) -> Optional[str]:
        """
        获取对话组对应的conversation_id
        
        Args:
            conversation_group_id: 对话组ID
            
        Returns:
            conversation_id，如果是新对话则返回None
        """
        return self._conversation_mapping.get(conversation_group_id)
    
    def set_conversation_id(self, conversation_group_id: str, conversation_id: str) -> None:
        """
        设置对话组的conversation_id
        
        Args:
            conversation_group_id: 对话组ID
            conversation_id: API返回的conversation_id
        """
        if conversation_group_id not in self._conversation_mapping:
            self._conversation_created_time[conversation_group_id] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.logger.info(f"创建新会话: {conversation_group_id} -> {conversation_id}")
        else:
            self.logger.debug(f"更新会话ID: {conversation_group_id} -> {conversation_id}")
        
        self._conversation_mapping[conversation_group_id] = conversation_id
    
    def is_new_conversation(self, conversation_group_id: str) -> bool:
        """
        判断是否为新对话
        
        Args:
            conversation_group_id: 对话组ID
            
        Returns:
            True表示新对话，False表示已存在的对话
        """
        return conversation_group_id not in self._conversation_mapping
    
    def add_turn(self, conversation_group_id: str, turn_number: int, 
                user_question: str, chatflow_reply: str, 
                api_status: str, error_details: str = "",
                response_time: float = 0.0) -> None:
        """
        添加对话轮次记录
        
        Args:
            conversation_group_id: 对话组ID
            turn_number: 轮次号
            user_question: 用户问题
            chatflow_reply: Chatflow回复
            api_status: API调用状态
            error_details: 错误详情
            response_time: 响应时间
        """
        if conversation_group_id not in self._conversation_turns:
            self._conversation_turns[conversation_group_id] = []
        
        turn_record = {
            'turn_number': turn_number,
            'user_question': user_question,
            'chatflow_reply': chatflow_reply,
            'api_status': api_status,
            'error_details': error_details,
            'response_time': response_time,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self._conversation_turns[conversation_group_id].append(turn_record)
        
        self.logger.debug(f"记录对话轮次: {conversation_group_id} 第{turn_number}轮")
    
    def get_conversation_turns(self, conversation_group_id: str) -> List[Dict[str, Any]]:
        """
        获取对话组的所有轮次记录
        
        Args:
            conversation_group_id: 对话组ID
            
        Returns:
            轮次记录列表
        """
        return self._conversation_turns.get(conversation_group_id, [])
    
    def get_last_turn(self, conversation_group_id: str) -> Optional[Dict[str, Any]]:
        """
        获取对话组的最后一轮记录
        
        Args:
            conversation_group_id: 对话组ID
            
        Returns:
            最后一轮记录，如果没有则返回None
        """
        turns = self._conversation_turns.get(conversation_group_id, [])
        return turns[-1] if turns else None
    
    def get_turn_count(self, conversation_group_id: str) -> int:
        """
        获取对话组的轮次数量
        
        Args:
            conversation_group_id: 对话组ID
            
        Returns:
            轮次数量
        """
        return len(self._conversation_turns.get(conversation_group_id, []))
    
    def validate_turn_sequence(self, conversation_group_id: str, expected_turn: int) -> bool:
        """
        验证轮次序列的正确性
        
        Args:
            conversation_group_id: 对话组ID
            expected_turn: 期望的轮次号
            
        Returns:
            True表示轮次序列正确，False表示有问题
        """
        current_turn_count = self.get_turn_count(conversation_group_id)
        
        # 第一轮应该是1，后续轮次应该连续
        if current_turn_count == 0:
            return expected_turn == 1
        else:
            return expected_turn == current_turn_count + 1
    
    def get_all_conversations(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有对话的摘要信息
        
        Returns:
            所有对话的摘要信息
        """
        summary = {}
        
        for group_id in self._conversation_mapping.keys():
            conversation_id = self._conversation_mapping[group_id]
            turn_count = self.get_turn_count(group_id)
            created_time = self._conversation_created_time.get(group_id, "未知")
            
            summary[group_id] = {
                'conversation_id': conversation_id,
                'turn_count': turn_count,
                'created_time': created_time,
                'last_turn': self.get_last_turn(group_id)
            }
        
        return summary
    
    def clear_conversation(self, conversation_group_id: str) -> None:
        """
        清除指定对话的所有记录
        
        Args:
            conversation_group_id: 对话组ID
        """
        if conversation_group_id in self._conversation_mapping:
            del self._conversation_mapping[conversation_group_id]
        
        if conversation_group_id in self._conversation_turns:
            del self._conversation_turns[conversation_group_id]
        
        if conversation_group_id in self._conversation_created_time:
            del self._conversation_created_time[conversation_group_id]
        
        self.logger.info(f"已清除对话记录: {conversation_group_id}")
    
    def clear_all_conversations(self) -> None:
        """
        清除所有对话记录
        """
        self._conversation_mapping.clear()
        self._conversation_turns.clear()
        self._conversation_created_time.clear()
        
        self.logger.info("已清除所有对话记录")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取会话管理统计信息
        
        Returns:
            统计信息字典
        """
        total_conversations = len(self._conversation_mapping)
        total_turns = sum(len(turns) for turns in self._conversation_turns.values())
        
        # 计算平均轮次数
        avg_turns = total_turns / total_conversations if total_conversations > 0 else 0
        
        # 统计成功和失败的轮次
        successful_turns = 0
        failed_turns = 0
        
        for turns in self._conversation_turns.values():
            for turn in turns:
                if turn.get('api_status') == '成功':
                    successful_turns += 1
                else:
                    failed_turns += 1
        
        # 计算成功率
        success_rate = (successful_turns / total_turns * 100) if total_turns > 0 else 0
        
        return {
            'total_conversations': total_conversations,
            'total_turns': total_turns,
            'average_turns_per_conversation': round(avg_turns, 2),
            'successful_turns': successful_turns,
            'failed_turns': failed_turns,
            'success_rate': round(success_rate, 2)
        }
    
    def export_conversation_history(self, conversation_group_id: str) -> List[Dict[str, Any]]:
        """
        导出指定对话的完整历史记录
        
        Args:
            conversation_group_id: 对话组ID
            
        Returns:
            完整的对话历史记录
        """
        conversation_id = self.get_conversation_id(conversation_group_id)
        turns = self.get_conversation_turns(conversation_group_id)
        created_time = self._conversation_created_time.get(conversation_group_id, "未知")
        
        return {
            'conversation_group_id': conversation_group_id,
            'conversation_id': conversation_id,
            'created_time': created_time,
            'turn_count': len(turns),
            'turns': turns
        }


if __name__ == "__main__":
    # 测试会话管理器
    import sys
    
    # 设置日志
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("会话管理器测试")
    
    manager = ConversationManager()
    
    # 测试新对话
    group_id = "test_001"
    print(f"是否为新对话: {manager.is_new_conversation(group_id)}")
    
    # 设置conversation_id
    manager.set_conversation_id(group_id, "conv_123456")
    print(f"获取conversation_id: {manager.get_conversation_id(group_id)}")
    
    # 添加对话轮次
    manager.add_turn(group_id, 1, "你好", "您好！", "成功", "", 1.2)
    manager.add_turn(group_id, 2, "今天天气怎么样？", "今天天气很好！", "成功", "", 0.8)
    
    # 获取统计信息
    stats = manager.get_statistics()
    print(f"统计信息: {stats}")
    
    # 获取对话摘要
    summary = manager.get_all_conversations()
    print(f"对话摘要: {summary}")
    
    print("测试完成！")