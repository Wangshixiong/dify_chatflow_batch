#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel文件处理模块
负责读取测试用例Excel文件和生成结果Excel文件
"""

import pandas as pd
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


class ExcelHandler:
    """Excel文件处理器"""
    
    # 输入文件必需的列名（支持中英文）
    REQUIRED_INPUT_COLUMNS = {
        '对话ID': 'conversation_group_id',
        '轮次': 'turn_number', 
        '用户问题': 'user_question',
        # 英文列名支持
        'conversation_id': 'conversation_group_id',
        'round': 'turn_number',
        'question': 'user_question'
    }
    
    # 输入文件可选的列名（支持中英文）
    OPTIONAL_INPUT_COLUMNS = {
        '期待回复': 'expected_reply',
        # 英文列名支持
        'expected_answer': 'expected_reply'
    }
    
    # 输出文件的列名
    OUTPUT_COLUMNS = {
        '对话ID': 'conversation_group_id',
        '轮次': 'turn_number',
        '用户问题': 'user_question', 
        '期待回复': 'expected_reply',
        'Chatflow回复答案': 'chatflow_reply',
        'API调用状态': 'api_status',
        '错误详情': 'error_details',
        '会话ID': 'conversation_id',
        '调用时间': 'call_time',
        '响应时间(秒)': 'response_time'
    }
    
    def __init__(self):
        """初始化Excel处理器"""
        pass
    
    def read_test_cases(self, file_path: str) -> List[Dict[str, Any]]:
        """
        读取测试用例Excel文件
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            测试用例列表，每个元素是一个字典
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式错误或缺少必要列
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"测试用例文件不存在: {file_path}")
        
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path, engine='openpyxl')
        except Exception as e:
            raise ValueError(f"读取Excel文件失败: {e}")
        
        # 验证必要的列是否存在
        self._validate_input_columns(df)
        
        # 数据清洗和验证
        df = self._clean_input_data(df)
        
        # 创建列名映射
        column_mapping = {}
        for col_name in df.columns:
            if col_name in self.REQUIRED_INPUT_COLUMNS:
                column_mapping[self.REQUIRED_INPUT_COLUMNS[col_name]] = col_name
            elif col_name in self.OPTIONAL_INPUT_COLUMNS:
                column_mapping[self.OPTIONAL_INPUT_COLUMNS[col_name]] = col_name
        
        # 转换为字典列表
        test_cases = []
        for index, row in df.iterrows():
            # 获取期待回复列名（可能是中文或英文）
            expected_reply_col = column_mapping.get('expected_reply')
            expected_reply = ''
            if expected_reply_col and expected_reply_col in row and pd.notna(row[expected_reply_col]):
                expected_reply = str(row[expected_reply_col]).strip()
            
            test_case = {
                'conversation_group_id': str(row[column_mapping['conversation_group_id']]).strip(),
                'turn_number': int(row[column_mapping['turn_number']]),
                'user_question': str(row[column_mapping['user_question']]).strip(),
                'expected_reply': expected_reply,
                'row_index': index + 2  # Excel行号（从2开始，因为第1行是标题）
            }
            test_cases.append(test_case)
        
        # 按对话ID和轮次排序
        test_cases.sort(key=lambda x: (x['conversation_group_id'], x['turn_number']))
        
        return test_cases
    
    def _validate_input_columns(self, df: pd.DataFrame) -> None:
        """
        验证输入文件的列名
        
        Args:
            df: pandas DataFrame
            
        Raises:
            ValueError: 缺少必要的列
        """
        # 检查是否有必需的列（中文或英文）
        required_fields = ['conversation_group_id', 'turn_number', 'user_question']
        found_fields = set()
        
        for col_name in df.columns:
            if col_name in self.REQUIRED_INPUT_COLUMNS:
                field_type = self.REQUIRED_INPUT_COLUMNS[col_name]
                found_fields.add(field_type)
        
        missing_fields = set(required_fields) - found_fields
        
        if missing_fields:
            # 提供中英文列名建议
            suggestions = []
            for field in missing_fields:
                if field == 'conversation_group_id':
                    suggestions.append('对话ID 或 conversation_id')
                elif field == 'turn_number':
                    suggestions.append('轮次 或 round')
                elif field == 'user_question':
                    suggestions.append('用户问题 或 question')
            
            raise ValueError(
                f"测试用例文件缺少必要的列: {', '.join(suggestions)}\n"
                f"当前列名: {', '.join(df.columns.tolist())}"
            )
    
    def _clean_input_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗和验证输入数据
        
        Args:
            df: pandas DataFrame
            
        Returns:
            清洗后的DataFrame
            
        Raises:
            ValueError: 数据验证失败
        """
        # 删除所有列都为空的行
        df = df.dropna(how='all')
        
        # 创建列名映射
        column_mapping = {}
        for col_name in df.columns:
            if col_name in self.REQUIRED_INPUT_COLUMNS:
                column_mapping[self.REQUIRED_INPUT_COLUMNS[col_name]] = col_name
        
        # 验证必要字段不能为空
        required_fields = ['conversation_group_id', 'turn_number', 'user_question']
        for field_type in required_fields:
            if field_type in column_mapping:
                col_name = column_mapping[field_type]
                empty_rows = df[df[col_name].isna() | (df[col_name].astype(str).str.strip() == '')]
                if not empty_rows.empty:
                    row_numbers = [idx + 2 for idx in empty_rows.index]  # Excel行号
                    raise ValueError(f"第{', '.join(map(str, row_numbers))}行的'{col_name}'字段不能为空")
        
        # 验证轮次必须是正整数
        if 'turn_number' in column_mapping:
            turn_col = column_mapping['turn_number']
            try:
                df[turn_col] = pd.to_numeric(df[turn_col], errors='coerce')
                invalid_turns = df[df[turn_col].isna() | (df[turn_col] <= 0) | (df[turn_col] != df[turn_col].astype(int))]
                if not invalid_turns.empty:
                    row_numbers = [idx + 2 for idx in invalid_turns.index]
                    raise ValueError(f"第{', '.join(map(str, row_numbers))}行的'{turn_col}'必须是正整数")
                df[turn_col] = df[turn_col].astype(int)
            except Exception as e:
                raise ValueError(f"轮次字段格式错误: {e}")
        
        return df
    
    def create_result_file(self, test_cases: List[Dict[str, Any]], 
                          output_dir: str = '.', 
                          include_timestamp: bool = True) -> str:
        """
        创建结果Excel文件
        
        Args:
            test_cases: 包含结果的测试用例列表
            output_dir: 输出目录
            include_timestamp: 是否在文件名中包含时间戳
            
        Returns:
            生成的文件路径
        """
        # 生成文件名
        if include_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"result_{timestamp}.xlsx"
        else:
            filename = "result.xlsx"
        
        file_path = os.path.join(output_dir, filename)
        
        # 准备数据
        result_data = []
        for case in test_cases:
            result_row = {
                '对话ID': case.get('conversation_group_id', ''),
                '轮次': case.get('turn_number', ''),
                '用户问题': case.get('user_question', ''),
                '期待回复': case.get('expected_reply', ''),
                'Chatflow回复答案': case.get('chatflow_reply', ''),
                'API调用状态': case.get('api_status', ''),
                '错误详情': case.get('error_details', ''),
                '会话ID': case.get('conversation_id', ''),
                '调用时间': case.get('call_time', ''),
                '响应时间(秒)': case.get('response_time', '')
            }
            result_data.append(result_row)
        
        # 创建DataFrame并保存
        df = pd.DataFrame(result_data)
        
        try:
            # 确保输出目录存在
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # 保存Excel文件
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='测试结果', index=False)
                
                # 调整列宽
                worksheet = writer.sheets['测试结果']
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)  # 最大宽度50
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            return file_path
            
        except Exception as e:
            raise ValueError(f"保存结果文件失败: {e}")
    
    def validate_test_case_structure(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        验证测试用例的结构和逻辑
        
        Args:
            test_cases: 测试用例列表
            
        Returns:
            验证结果统计信息
        """
        stats = {
            'total_cases': len(test_cases),
            'conversation_groups': set(),
            'turn_issues': [],
            'empty_questions': []
        }
        
        # 按对话ID分组检查
        conversation_groups = {}
        for case in test_cases:
            group_id = case['conversation_group_id']
            if group_id not in conversation_groups:
                conversation_groups[group_id] = []
            conversation_groups[group_id].append(case)
        
        stats['conversation_groups'] = set(conversation_groups.keys())
        
        # 检查每个对话组的轮次连续性
        for group_id, cases in conversation_groups.items():
            cases.sort(key=lambda x: x['turn_number'])
            
            # 检查轮次是否从1开始且连续
            expected_turn = 1
            for case in cases:
                if case['turn_number'] != expected_turn:
                    stats['turn_issues'].append({
                        'conversation_id': group_id,
                        'expected_turn': expected_turn,
                        'actual_turn': case['turn_number'],
                        'row_index': case.get('row_index', 'unknown')
                    })
                expected_turn += 1
            
            # 检查空问题
            for case in cases:
                if not case['user_question'].strip():
                    stats['empty_questions'].append({
                        'conversation_id': group_id,
                        'turn_number': case['turn_number'],
                        'row_index': case.get('row_index', 'unknown')
                    })
        
        # 判断是否有严重错误
        has_errors = len(stats['turn_issues']) > 0 or len(stats['empty_questions']) > 0
        
        return {
            'valid': not has_errors,
            'errors': stats['turn_issues'] + stats['empty_questions'],
            'stats': stats
        }
    
    def append_result_to_file(self, test_case: Dict[str, Any], file_path: str) -> bool:
        """
        将单个测试结果追加到Excel文件
        
        Args:
            test_case: 包含结果的测试用例
            file_path: 输出文件路径
            
        Returns:
            bool: 写入是否成功
        """
        try:
            # 准备单行数据
            result_row = {
                '对话ID': test_case.get('conversation_group_id', ''),
                '轮次': test_case.get('turn_number', ''),
                '用户问题': test_case.get('user_question', ''),
                '期待回复': test_case.get('expected_reply', ''),
                'Chatflow回复答案': test_case.get('chatflow_reply', ''),
                'API调用状态': test_case.get('api_status', ''),
                '错误详情': test_case.get('error_details', ''),
                '会话ID': test_case.get('conversation_id', ''),
                '调用时间': test_case.get('call_time', ''),
                '响应时间(秒)': test_case.get('response_time', '')
            }
            
            # 检查文件是否存在
            if os.path.exists(file_path):
                # 文件存在，追加数据
                existing_df = pd.read_excel(file_path, engine='openpyxl')
                new_df = pd.DataFrame([result_row])
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            else:
                # 文件不存在，创建新文件
                combined_df = pd.DataFrame([result_row])
                # 确保输出目录存在
                Path(os.path.dirname(file_path)).mkdir(parents=True, exist_ok=True)
            
            # 保存文件
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                combined_df.to_excel(writer, sheet_name='测试结果', index=False)
                
                # 调整列宽
                worksheet = writer.sheets['测试结果']
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            return True
            
        except Exception as e:
            print(f"写入结果文件失败: {e}")
            return False


if __name__ == "__main__":
    # 测试Excel处理器
    handler = ExcelHandler()
    
    # 创建示例测试用例
    sample_cases = [
        {
            'conversation_group_id': 'test_001',
            'turn_number': 1,
            'user_question': '你好',
            'expected_reply': '您好！',
            'chatflow_reply': '您好！有什么可以帮助您的吗？',
            'api_status': '成功',
            'error_details': '',
            'conversation_id': 'conv_123',
            'call_time': '2025-01-05 14:30:22',
            'response_time': 1.2
        }
    ]
    
    try:
        result_file = handler.create_result_file(sample_cases, '.', True)
        print(f"示例结果文件已创建: {result_file}")
    except Exception as e:
        print(f"创建示例文件失败: {e}")