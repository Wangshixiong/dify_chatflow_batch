"""
现有模块封装器
导入并封装现有的命令行工具模块，提供Web API使用
"""
import sys
import os
from pathlib import Path
import logging
from typing import Dict, Any, Optional, List, TYPE_CHECKING

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

logger = logging.getLogger(__name__)

# 类型检查时的导入
if TYPE_CHECKING:
    try:
        from config_manager import ConfigManager as RealConfigManager  # type: ignore
        from excel_handler import ExcelHandler as RealExcelHandler  # type: ignore
        from dify_client import DifyClient as RealDifyClient  # type: ignore
        from conversation_manager import ConversationManager as RealConversationManager  # type: ignore
        from logger import LoggerManager  # type: ignore
    except ImportError:
        # 如果类型检查时导入失败，使用Any
        from typing import Any as RealConfigManager, Any as RealExcelHandler
        from typing import Any as RealDifyClient, Any as RealConversationManager
        LoggerManager = Any

try:
    # 导入现有模块
    from config_manager import ConfigManager  # type: ignore
    from excel_handler import ExcelHandler  # type: ignore
    from dify_client import DifyClient  # type: ignore
    from conversation_manager import ConversationManager  # type: ignore
    from logger import LoggerManager  # type: ignore
    
    logger.info("现有模块导入成功")
    LEGACY_MODULES_AVAILABLE = True
    
except ImportError as e:
    logger.error(f"导入现有模块失败: {e}")
    LEGACY_MODULES_AVAILABLE = False
    
    # 创建占位符类，避免导入错误
    from typing import Dict, Any
    
    class ConfigManager:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("现有模块不可用")
        
        def get_api_config(self) -> Dict[str, Any]:
            """获取API配置"""
            raise NotImplementedError("现有模块不可用")
        
        def get_response_mode(self) -> str:
            """获取响应模式"""
            raise NotImplementedError("现有模块不可用")
    
    class ExcelHandler:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("现有模块不可用")
        
        def read_test_cases(self, file_path: str) -> List[Dict[str, Any]]:
            """读取测试用例"""
            raise NotImplementedError("现有模块不可用")
    
    class DifyClient:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("现有模块不可用")
        
        def send_message(self, message: str, conversation_id: str, user_id: str) -> Dict[str, Any]:
            """发送消息"""
            raise NotImplementedError("现有模块不可用")
    
    class ConversationManager:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("现有模块不可用")

class LegacyServiceWrapper:
    """现有服务的封装器"""
    
    def __init__(self):
        self.available = LEGACY_MODULES_AVAILABLE
        if not self.available:
            logger.warning("现有模块不可用，某些功能将受限")
    
    def create_config_manager(self, config_path: Optional[str] = None) -> "ConfigManager":
        """创建配置管理器"""
        if not self.available:
            raise RuntimeError("现有模块不可用")
        return ConfigManager(config_path)
    
    def create_excel_handler(self) -> ExcelHandler:
        """创建Excel处理器"""
        if not self.available:
            raise RuntimeError("现有模块不可用")
        return ExcelHandler()
    
    def create_dify_client(self, config_manager: ConfigManager) -> DifyClient:
        """创建Dify客户端"""
        if not self.available:
            raise RuntimeError("现有模块不可用")
        return DifyClient(config_manager)
    
    def create_conversation_manager(self) -> ConversationManager:
        """创建对话管理器"""
        if not self.available:
            raise RuntimeError("现有模块不可用")
        return ConversationManager()
    
    def test_api_connection(self, api_url: str, api_key: str, timeout: int = 30) -> dict:
        """测试API连接"""
        if not self.available:
            return {
                "success": False,
                "message": "现有模块不可用，无法测试连接"
            }
        
        try:
            # 创建临时配置
            import tempfile
            import configparser
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
                config = configparser.ConfigParser()
                config['API'] = {
                    'API_URL': api_url,
                    'API_KEY': api_key,
                    'USER_ID': 'test_user',
                    'TIMEOUT': str(timeout),
                    'RESPONSE_MODE': 'blocking'
                }
                config['LOGGING'] = {
                    'LOG_LEVEL': 'ERROR',
                    'LOG_FILE': ''
                }
                config['OUTPUT'] = {
                    'OUTPUT_DIR': '',
                    'INCLUDE_TIMESTAMP': 'false'
                }
                config.write(f)
                temp_config_path = f.name
            
            # 测试连接
            config_manager = ConfigManager(temp_config_path)
            dify_client = DifyClient(config_manager)
            
            # 发送测试请求
            import time
            start_time = time.time()
            
            test_response = dify_client.send_message(
                message="test",
                conversation_id="test_connection",
                user_id="test_user"
            )
            
            response_time = time.time() - start_time
            
            # 清理临时文件
            os.unlink(temp_config_path)
            
            if test_response and not test_response.get('error'):
                return {
                    "success": True,
                    "message": "连接测试成功",
                    "response_time": round(response_time, 2)
                }
            else:
                return {
                    "success": False,
                    "message": f"API返回错误: {test_response.get('error', '未知错误')}"
                }
                
        except Exception as e:
            # 清理临时文件
            temp_config_path = None
            try:
                if 'temp_config_path' in locals() and temp_config_path:
                    os.unlink(temp_config_path)
            except:
                pass
            
            return {
                "success": False,
                "message": f"连接测试失败: {str(e)}"
            }
    
    def parse_excel_file(self, file_path: str) -> dict:
        """解析Excel测试用例文件"""
        if not self.available:
            return {
                "success": False,
                "message": "现有模块不可用",
                "cases": []
            }
        
        try:
            excel_handler = ExcelHandler()
            test_cases = excel_handler.read_test_cases(file_path)
            
            # 转换为Web格式
            web_cases = []
            for case in test_cases:
                web_case = {
                    "conversation_id": case.get("conversation_group_id", ""),
                    "round": case.get("turn_number", 1),
                    "user_question": case.get("user_question", ""),
                    "expected_response": case.get("expected_reply", ""),
                    "inputs": case.get("inputs", "")
                }
                web_cases.append(web_case)
            
            return {
                "success": True,
                "message": f"成功解析 {len(web_cases)} 条测试用例",
                "cases": web_cases
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"解析Excel文件失败: {str(e)}",
                "cases": []
            }

# 全局封装器实例
legacy_wrapper = LegacyServiceWrapper()