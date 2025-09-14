"""
文件存储管理器
使用简单的文件存储替代数据库
"""
import os
import json
import configparser
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

class FileStorageManager:
    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            self.data_dir = Path(__file__).parent.parent / "data"
        else:
            self.data_dir = Path(data_dir)
        
        # 创建必要的目录
        self.configs_dir = self.data_dir / "configs"
        self.configs_dir.mkdir(parents=True, exist_ok=True)
        
        # 文件路径
        self.test_cases_file = self.data_dir / "test_cases.json"
        self.test_history_file = self.data_dir / "test_history.json"
        self.settings_file = self.data_dir / "settings.json"
        
        # 初始化文件
        self._init_files()
    
    def _init_files(self):
        """初始化存储文件"""
        # 初始化测试用例文件
        if not self.test_cases_file.exists():
            self._save_json(self.test_cases_file, [])
        
        # 初始化测试历史文件
        if not self.test_history_file.exists():
            self._save_json(self.test_history_file, [])
        
        # 初始化设置文件
        if not self.settings_file.exists():
            default_settings = {
                "active_config": "default",
                "ui_preferences": {
                    "theme": "light",
                    "auto_scroll_logs": True,
                    "max_log_lines": 500
                },
                "created_at": datetime.now().isoformat()
            }
            self._save_json(self.settings_file, default_settings)
        
        # 检查并导入根目录的config.ini
        self._import_root_config()
    
    def _import_root_config(self):
        """首次启动时导入根目录的config.ini作为默认配置"""
        default_config_path = self.configs_dir / "default.ini"
        root_config_path = Path(__file__).parent.parent.parent / "config.ini"
        
        if not default_config_path.exists() and root_config_path.exists():
            try:
                # 读取根目录配置文件
                import configparser
                root_config = configparser.ConfigParser()
                root_config.read(root_config_path, encoding='utf-8')
                
                # 检查是否有API_KEY需要加密
                if 'API' in root_config and 'API_KEY' in root_config['API']:
                    api_key = root_config['API']['API_KEY']
                    
                    # 导入安全模块进行加密
                    try:
                        from security import security
                        encrypted_key = security.encrypt_api_key(api_key)
                        
                        # 创建加密后的配置数据
                        config_data = {
                            'api_url': root_config['API'].get('API_URL', ''),
                            'api_key': encrypted_key,
                            'user_id': root_config['API'].get('USER_ID', 'test_user'),
                            'timeout': int(root_config['API'].get('TIMEOUT', 120)),
                            'response_mode': root_config['API'].get('RESPONSE_MODE', 'streaming'),
                            'log_level': root_config['LOGGING'].get('LOG_LEVEL', 'INFO') if 'LOGGING' in root_config else 'INFO',
                            'output_dir': root_config['OUTPUT'].get('OUTPUT_DIR', '') if 'OUTPUT' in root_config else '',
                            'include_timestamp': (root_config['OUTPUT'].get('INCLUDE_TIMESTAMP', 'true') if 'OUTPUT' in root_config else 'true').lower() == 'true'
                        }
                        
                        # 使用save_config方法保存（它会自动格式化为.ini格式）
                        self.save_config('default', config_data)
                        logger.info(f"已导入并加密根目录配置文件: {root_config_path} -> {default_config_path}")
                        
                    except Exception as e:
                        logger.warning(f"加密API密钥失败，使用原始文件: {e}")
                        # 如果加密失败，回退到直接复制
                        shutil.copy2(root_config_path, default_config_path)
                        logger.info(f"已导入根目录配置文件（未加密）: {root_config_path} -> {default_config_path}")
                else:
                    # 如果没有API_KEY，直接复制
                    shutil.copy2(root_config_path, default_config_path)
                    logger.info(f"已导入根目录配置文件: {root_config_path} -> {default_config_path}")
                    
            except Exception as e:
                logger.warning(f"导入根目录配置文件失败: {e}")
    
    def _load_json(self, file_path: Path) -> Any:
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载JSON文件失败 {file_path}: {e}")
            return None
    
    def _save_json(self, file_path: Path, data: Any):
        """保存JSON文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error(f"保存JSON文件失败 {file_path}: {e}")
            raise
    
    # 配置管理
    def list_configs(self) -> List[Dict]:
        """获取所有配置列表"""
        configs = []
        settings = self._load_json(self.settings_file) or {}
        active_config = settings.get("active_config", "default")
        
        for config_file in self.configs_dir.glob("*.ini"):
            config_name = config_file.stem
            config_data = self._load_config(config_name)
            if config_data:
                configs.append({
                    "id": config_name,
                    "name": config_name,
                    "is_active": config_name == active_config,
                    "created_at": datetime.fromtimestamp(config_file.stat().st_ctime).isoformat(),
                    "updated_at": datetime.fromtimestamp(config_file.stat().st_mtime).isoformat(),
                    **config_data
                })
        
        return configs
    
    def _load_config(self, config_name: str) -> Optional[Dict]:
        """加载单个配置文件"""
        config_path = self.configs_dir / f"{config_name}.ini"
        if not config_path.exists():
            return None
        
        try:
            config = configparser.ConfigParser()
            config.read(config_path, encoding='utf-8')
            
            # 转换为字典格式
            result = {}
            for section in config.sections():
                for key, value in config[section].items():
                    # 处理布尔值
                    if value.lower() in ('true', 'false'):
                        result[key] = value.lower() == 'true'
                    # 处理数字
                    elif value.isdigit():
                        result[key] = int(value)
                    else:
                        result[key] = value
            
            # 检查API_KEY是否需要加密（兼容性处理）
            if 'api_key' in result:
                api_key = result['api_key']
                # 简单判断：如果密钥看起来像明文（以app-开头且长度合理），则加密它
                if api_key.startswith('app-') and len(api_key) < 100:
                    try:
                        from security import security
                        encrypted_key = security.encrypt_api_key(api_key)
                        result['api_key'] = encrypted_key
                        
                        # 重新保存配置文件（更新为加密版本）
                        self.save_config(config_name, result)
                        logger.info(f"配置 {config_name} 的API密钥已自动加密")
                    except Exception as e:
                        logger.warning(f"自动加密API密钥失败: {e}")
            
            return result
        except Exception as e:
            logger.error(f"加载配置文件失败 {config_path}: {e}")
            return None
    
    def save_config(self, config_name: str, config_data: Dict) -> bool:
        """保存配置文件"""
        config_path = self.configs_dir / f"{config_name}.ini"
        
        try:
            config = configparser.ConfigParser()
            
            # 按原有格式组织配置
            config['API'] = {
                'API_URL': config_data.get('api_url', ''),
                'API_KEY': config_data.get('api_key', ''),
                'USER_ID': config_data.get('user_id', 'test_user'),
                'TIMEOUT': str(config_data.get('timeout', 120)),
                'RESPONSE_MODE': config_data.get('response_mode', 'streaming')
            }
            
            config['LOGGING'] = {
                'LOG_LEVEL': config_data.get('log_level', 'INFO'),
                'LOG_FILE': ''
            }
            
            config['OUTPUT'] = {
                'OUTPUT_DIR': config_data.get('output_dir', ''),
                'INCLUDE_TIMESTAMP': str(config_data.get('include_timestamp', True)).lower()
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                config.write(f)
            
            logger.info(f"配置文件保存成功: {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置文件失败 {config_path}: {e}")
            return False
    
    def delete_config(self, config_name: str) -> bool:
        """删除配置文件"""
        if config_name == "default":
            return False  # 不允许删除默认配置
        
        config_path = self.configs_dir / f"{config_name}.ini"
        try:
            if config_path.exists():
                config_path.unlink()
                logger.info(f"配置文件删除成功: {config_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"删除配置文件失败 {config_path}: {e}")
            return False
    
    def set_active_config(self, config_name: str):
        """设置活跃配置"""
        settings = self._load_json(self.settings_file) or {}
        settings["active_config"] = config_name
        self._save_json(self.settings_file, settings)
    
    # 测试用例管理
    def get_test_cases(self) -> List[Dict]:
        """获取测试用例列表"""
        return self._load_json(self.test_cases_file) or []
    
    def save_test_cases(self, cases: List[Dict]):
        """保存测试用例列表"""
        # 为每个用例添加ID和时间戳
        for case in cases:
            if 'id' not in case:
                case['id'] = str(uuid.uuid4())
            if 'created_at' not in case:
                case['created_at'] = datetime.now().isoformat()
            case['updated_at'] = datetime.now().isoformat()
        
        self._save_json(self.test_cases_file, cases)
    
    def add_test_case(self, case_data: Dict) -> str:
        """添加单个测试用例"""
        cases = self.get_test_cases()
        case_id = str(uuid.uuid4())
        case_data.update({
            'id': case_id,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        })
        cases.append(case_data)
        self.save_test_cases(cases)
        return case_id
    
    def update_test_case(self, case_id: str, case_data: Dict) -> bool:
        """更新测试用例"""
        cases = self.get_test_cases()
        for case in cases:
            if case['id'] == case_id:
                case.update(case_data)
                case['updated_at'] = datetime.now().isoformat()
                self.save_test_cases(cases)
                return True
        return False
    
    def delete_test_case(self, case_id: str) -> bool:
        """删除测试用例"""
        cases = self.get_test_cases()
        original_length = len(cases)
        cases = [case for case in cases if case['id'] != case_id]
        if len(cases) < original_length:
            self.save_test_cases(cases)
            return True
        return False
    
    # 测试历史管理
    def get_test_history(self) -> List[Dict]:
        """获取测试历史"""
        return self._load_json(self.test_history_file) or []
    
    def add_test_record(self, record: Dict) -> str:
        """添加测试记录"""
        history = self.get_test_history()
        record_id = str(uuid.uuid4())
        record.update({
            'id': record_id,
            'created_at': datetime.now().isoformat()
        })
        history.append(record)
        
        # 只保留最近100条记录
        if len(history) > 100:
            history = history[-100:]
        
        self._save_json(self.test_history_file, history)
        return record_id
    
    def get_test_record(self, record_id: str) -> Optional[Dict]:
        """获取单个测试记录"""
        history = self.get_test_history()
        return next((record for record in history if record['id'] == record_id), None)
    
    def delete_test_record(self, record_id: str) -> bool:
        """删除测试记录"""
        history = self.get_test_history()
        original_length = len(history)
        history = [record for record in history if record['id'] != record_id]
        if len(history) < original_length:
            self._save_json(self.test_history_file, history)
            return True
        return False
    
    def get_test_results(self, task_id: Optional[str] = None) -> List[Dict]:
        """获取测试结果（从历史记录中提取）"""
        history = self.get_test_history()
        if task_id:
            # 获取特定任务的结果
            record = next((r for r in history if r.get('task_id') == task_id), None)
            return record.get('results', []) if record else []
        else:
            # 获取所有结果
            all_results = []
            for record in history:
                results = record.get('results', [])
                # 为每个结果添加任务信息
                for result in results:
                    result['task_info'] = {
                        'task_id': record.get('task_id'),
                        'config_name': record.get('config_name'),
                        'created_at': record.get('created_at')
                    }
                all_results.extend(results)
            return all_results
    
    def export_results(self, task_id: Optional[str] = None, format: str = 'excel', scope: str = 'all') -> Dict:
        """导出测试结果"""
        results = self.get_test_results(task_id)
        
        # 根据scope过滤结果
        if scope == 'success':
            results = [r for r in results if r.get('api_status') == 'success']
        elif scope == 'failed':
            results = [r for r in results if r.get('api_status') != 'success']
        
        if not results:
            return {'success': False, 'message': '没有可导出的结果'}
        
        try:
            if format == 'excel':
                return self._export_to_excel(results, task_id)
            elif format == 'csv':
                return self._export_to_csv(results, task_id)
            elif format == 'json':
                return self._export_to_json(results, task_id)
            else:
                return {'success': False, 'message': '不支持的导出格式'}
        except Exception as e:
            logger.error(f"导出结果失败: {e}")
            return {'success': False, 'message': f'导出失败: {str(e)}'}
    
    def _export_to_excel(self, results: List[Dict], task_id: Optional[str] = None) -> Dict:
        """导出为Excel格式"""
        import pandas as pd
        import tempfile
        
        # 准备数据，使用与原始Python脚本相同的字段结构
        export_data = []
        for result in results:
            export_data.append({
                '对话ID': result.get('conversation_id', ''),
                '轮次': result.get('turn_number', ''),
                '用户问题': result.get('user_question', ''),
                '期待回复': result.get('expected_response', ''),
                'Chatflow回复答案': result.get('chatflow_reply', ''),
                'API调用状态': result.get('api_status', ''),
                '错误详情': result.get('error_details', ''),
                '会话ID': result.get('conversation_id', ''),  # 这里可能是内部conversation_id
                '调用时间': result.get('call_time', ''),
                '响应时间(秒)': result.get('response_time', '')
            })
        
        df = pd.DataFrame(export_data)
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            # 直接使用 DataFrame.to_excel，绕过 pandas ExcelWriter 抽象类问题
            df.to_excel(tmp.name, sheet_name='测试结果', index=False, engine='openpyxl')
            
            # 生成类似原始格式的文件名: result_YYYYMMDD_HHMMSS.xlsx
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"result_{timestamp}.xlsx"
            
            return {
                'success': True,
                'file_path': tmp.name,
                'filename': filename,
                'count': len(results)
            }
    
    def _export_to_csv(self, results: List[Dict], task_id: Optional[str] = None) -> Dict:
        """导出为CSV格式"""
        import pandas as pd
        import tempfile
        
        # 准备数据（与原始Python脚本相同Excel格式）
        export_data = []
        for result in results:
            export_data.append({
                '对话ID': result.get('conversation_id', ''),
                '轮次': result.get('turn_number', ''),
                '用户问题': result.get('user_question', ''),
                '期待回复': result.get('expected_response', ''),
                'Chatflow回复答案': result.get('chatflow_reply', ''),
                'API调用状态': result.get('api_status', ''),
                '错误详情': result.get('error_details', ''),
                '会话ID': result.get('conversation_id', ''),  # 这里可能是内部conversation_id
                '调用时间': result.get('call_time', ''),
                '响应时间(秒)': result.get('response_time', '')
            })
        
        df = pd.DataFrame(export_data)
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w', encoding='utf-8-sig') as tmp:
            df.to_csv(tmp.name, index=False, encoding='utf-8-sig')
            filename = f"test_results_{task_id or 'all'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            return {
                'success': True,
                'file_path': tmp.name,
                'filename': filename,
                'count': len(results)
            }
    
    def _export_to_json(self, results: List[Dict], task_id: Optional[str] = None) -> Dict:
        """导出为JSON格式"""
        import tempfile
        
        export_data = {
            'export_info': {
                'task_id': task_id,
                'export_time': datetime.now().isoformat(),
                'count': len(results)
            },
            'results': results
        }
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w', encoding='utf-8') as tmp:
            json.dump(export_data, tmp, ensure_ascii=False, indent=2, default=str)
            filename = f"test_results_{task_id or 'all'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            return {
                'success': True,
                'file_path': tmp.name,
                'filename': filename,
                'count': len(results)
            }
    
    # 设置管理
    def get_settings(self) -> Dict:
        """获取系统设置"""
        return self._load_json(self.settings_file) or {}
    
    def update_settings(self, settings: Dict):
        """更新系统设置"""
        current_settings = self.get_settings()
        current_settings.update(settings)
        self._save_json(self.settings_file, current_settings)

# 全局存储管理器实例
storage = FileStorageManager()