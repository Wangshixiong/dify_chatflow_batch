"""
数据模型定义
使用Pydantic进行严格的数据验证
"""
from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum
import re

# 枚举定义
class ResponseMode(str, Enum):
    STREAMING = "streaming"
    BLOCKING = "blocking"

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

class TaskStatus(str, Enum):
    PREPARING = "preparing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"
    FAILED = "failed"

class TestResultStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

# 配置相关模型
class ConfigBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="配置名称")
    api_url: HttpUrl = Field(..., description="API地址")
    api_key: str = Field(..., min_length=1, description="API密钥")
    user_id: str = Field(default="test_user", min_length=1, max_length=100)
    timeout: int = Field(default=120, ge=10, le=300, description="超时时间(秒)")
    response_mode: ResponseMode = Field(default=ResponseMode.STREAMING)
    log_level: LogLevel = Field(default=LogLevel.INFO)
    output_dir: Optional[str] = Field(default="", max_length=500)
    include_timestamp: bool = Field(default=True)
    
    @validator('name')
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fff\-\.]+$', v):
            raise ValueError('配置名称只能包含字母、数字、中文、下划线、连字符和点号')
        return v
    
    @validator('api_key')
    def validate_api_key(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('API密钥长度不能少于10个字符')
        return v.strip()
    
    @validator('output_dir')
    def validate_output_dir(cls, v):
        if v and not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fff\-\.\\/\\\\:]+$', v):
            raise ValueError('输出目录路径包含非法字符')
        return v

class ConfigCreate(ConfigBase):
    pass

class ConfigUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    api_url: Optional[HttpUrl] = None
    api_key: Optional[str] = Field(None, min_length=1)
    user_id: Optional[str] = Field(None, min_length=1, max_length=100)
    timeout: Optional[int] = Field(None, ge=10, le=300)
    response_mode: Optional[ResponseMode] = None
    log_level: Optional[LogLevel] = None
    output_dir: Optional[str] = Field(None, max_length=500)
    include_timestamp: Optional[bool] = None

class Config(ConfigBase):
    id: str
    api_key_masked: str = Field(..., description="遮蔽后的API密钥")
    created_at: datetime
    updated_at: datetime
    is_active: bool = Field(default=False)
    
    class Config:
        from_attributes = True

# 测试用例相关模型
class TestCaseBase(BaseModel):
    conversation_id: str = Field(..., min_length=1, max_length=100, description="对话ID")
    round: int = Field(..., ge=1, description="轮次")
    user_question: str = Field(..., min_length=1, max_length=10000, description="用户问题")
    expected_response: Optional[str] = Field(None, max_length=50000, description="期待回复")
    inputs: Optional[str] = Field(None, description="额外输入参数(JSON)")
    
    @validator('conversation_id')
    def validate_conversation_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fff\-]+$', v):
            raise ValueError('对话ID只能包含字母、数字、中文、下划线和连字符')
        return v
    
    @validator('inputs')
    def validate_inputs(cls, v):
        if v:
            try:
                import json
                json.loads(v)
            except json.JSONDecodeError:
                raise ValueError('inputs必须是有效的JSON字符串')
        return v

class TestCaseCreate(TestCaseBase):
    pass

class TestCaseUpdate(BaseModel):
    conversation_id: Optional[str] = Field(None, min_length=1, max_length=100)
    round: Optional[int] = Field(None, ge=1)
    user_question: Optional[str] = Field(None, min_length=1, max_length=10000)
    expected_response: Optional[str] = Field(None, max_length=50000)
    inputs: Optional[str] = None

class TestCase(TestCaseBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 测试任务相关模型
class TestTaskCreate(BaseModel):
    config_id: str = Field(..., description="配置ID")
    case_ids: List[str] = Field(..., min_items=1, description="测试用例ID列表")

class TestTaskProgress(BaseModel):
    total: int = Field(..., ge=0)
    completed: int = Field(..., ge=0)
    success: int = Field(..., ge=0)
    failed: int = Field(..., ge=0)
    current_case_id: Optional[str] = None
    
    @validator('completed')
    def validate_completed(cls, v, values):
        if 'total' in values and v > values['total']:
            raise ValueError('已完成数量不能超过总数量')
        return v

class TestTask(BaseModel):
    id: str
    config_id: str
    status: TaskStatus
    progress: TestTaskProgress
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# 测试结果相关模型
class TestResultCreate(BaseModel):
    task_id: str
    case_id: str
    status: TestResultStatus
    response: Optional[str] = None
    response_time: Optional[float] = Field(None, ge=0)
    error_message: Optional[str] = None

class TestResult(TestResultCreate):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# API响应模型
class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int = Field(..., ge=1)
    size: int = Field(..., ge=1, le=100)
    pages: int

# 文件上传相关
class FileUploadResponse(BaseModel):
    filename: str
    size: int
    cases_count: int
    success: bool
    message: str

# 导出相关
class ExportRequest(BaseModel):
    format: Literal["excel", "csv", "json"] = Field(default="excel")
    scope: Literal["all", "success", "failed"] = Field(default="all")
    task_id: Optional[str] = None

# 连接测试
class ConnectionTestRequest(BaseModel):
    api_url: HttpUrl
    api_key: str
    timeout: int = Field(default=30, ge=5, le=120)

class ConnectionTestResponse(BaseModel):
    success: bool
    message: str
    response_time: Optional[float] = None