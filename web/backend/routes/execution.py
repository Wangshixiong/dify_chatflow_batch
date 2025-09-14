"""
测试执行相关的API路由
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
import asyncio
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import tempfile
import os
import configparser

try:
    from ..models.schemas import ApiResponse
    from ..storage import storage
    from ..security import security
    from ..services.legacy_wrapper import legacy_wrapper
except ImportError:
    from models.schemas import ApiResponse
    from storage import storage
    from security import security
    from services.legacy_wrapper import legacy_wrapper

router = APIRouter(prefix="/api/test", tags=["execution"])

# 全局执行状态
execution_state = {
    "status": "idle",  # idle, running, paused, stopped, completed, error
    "task_id": None,
    "progress": {
        "total": 0,
        "completed": 0,
        "success": 0,
        "failed": 0,
        "current": None
    },
    "start_time": None,
    "end_time": None,
    "statistics": {
        "total_time": 0,
        "avg_response_time": 0,
        "min_response_time": 0,
        "max_response_time": 0,
        "success_rate": 0
    },
    "logs": [],
    "current_response": ""
}

def add_log(level: str, message: str):
    """添加日志"""
    log_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "level": level,
        "message": message
    }
    execution_state["logs"].append(log_entry)
    # 只保留最近100条日志
    if len(execution_state["logs"]) > 100:
        execution_state["logs"] = execution_state["logs"][-100:]

@router.post("/start")
async def start_test(background_tasks: BackgroundTasks):
    """开始测试"""
    if execution_state["status"] == "running":
        raise HTTPException(status_code=400, detail="测试已在运行中")
    
    # 获取测试用例
    test_cases = storage.get_test_cases()
    if not test_cases:
        raise HTTPException(status_code=400, detail="没有可用的测试用例")
    
    # 获取活跃配置
    configs = storage.list_configs()
    active_config = next((c for c in configs if c.get('is_active')), None)
    if not active_config:
        raise HTTPException(status_code=400, detail="没有活跃的配置")
    
    # 初始化执行状态
    task_id = str(uuid.uuid4())
    execution_state.update({
        "status": "running",
        "task_id": task_id,
        "progress": {
            "total": len(test_cases),
            "completed": 0,
            "success": 0,
            "failed": 0,
            "current": None
        },
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "statistics": {
            "total_time": 0,
            "avg_response_time": 0,
            "min_response_time": 0,
            "max_response_time": 0,
            "success_rate": 0
        },
        "logs": [],
        "current_response": ""
    })
    
    add_log("info", f"开始执行批量测试，共 {len(test_cases)} 条用例")
    add_log("info", f"使用配置: {active_config['name']}")
    
    # 在后台执行测试
    background_tasks.add_task(execute_test_cases, test_cases, active_config)
    
    return ApiResponse(success=True, message="测试已开始", data={"task_id": task_id})

@router.post("/pause")
async def pause_test():
    """暂停测试"""
    if execution_state["status"] != "running":
        raise HTTPException(status_code=400, detail="测试未在运行中")
    
    execution_state["status"] = "paused"
    add_log("warning", "测试已暂停")
    
    return ApiResponse(success=True, message="测试已暂停")

@router.post("/resume")
async def resume_test():
    """恢复测试"""
    if execution_state["status"] != "paused":
        raise HTTPException(status_code=400, detail="测试未处于暂停状态")
    
    execution_state["status"] = "running"
    add_log("info", "测试已恢复")
    
    return ApiResponse(success=True, message="测试已恢复")

@router.post("/stop")
async def stop_test():
    """停止测试"""
    if execution_state["status"] not in ["running", "paused"]:
        raise HTTPException(status_code=400, detail="测试未在执行中")
    
    execution_state["status"] = "stopped"
    execution_state["end_time"] = datetime.now().isoformat()
    add_log("error", "测试已停止")
    
    return ApiResponse(success=True, message="测试已停止")

@router.get("/status")
async def get_test_status():
    """获取测试状态"""
    return ApiResponse(success=True, message="获取状态成功", data=execution_state)

@router.get("/logs")
async def get_test_logs(limit: int = 50):
    """获取测试日志"""
    logs = execution_state["logs"][-limit:] if limit > 0 else execution_state["logs"]
    return ApiResponse(success=True, message="获取日志成功", data=logs)

@router.get("/stream")
async def stream_test_status():
    """实时推送测试状态 (Server-Sent Events)"""
    async def event_stream():
        while True:
            # 发送当前状态
            data = json.dumps(execution_state)
            yield f"data: {data}\n\n"
            
            # 如果测试完成或停止，结束流
            if execution_state["status"] in ["completed", "stopped", "error"]:
                break
                
            await asyncio.sleep(1)  # 每秒推送一次
    
    return StreamingResponse(
        event_stream(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

async def execute_test_cases(test_cases: list, config: dict):
    """执行测试用例 - 使用真实的执行引擎"""
    task_id = execution_state["task_id"]
    results = []
    response_times = []
    
    try:
        if not legacy_wrapper.available:
            raise Exception("现有模块不可用，无法执行测试")
        
        # 解密API密钥
        api_key = config.get('api_key') or ''
        decrypted_key = security.decrypt_api_key(api_key)
        
        # 创建临时配置文件
        temp_config_path = None
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            temp_config = configparser.ConfigParser()
            temp_config['API'] = {
                'API_URL': config.get('api_url', ''),
                'API_KEY': decrypted_key,
                'USER_ID': config.get('user_id', 'test_user'),
                'TIMEOUT': str(config.get('timeout', 120)),
                'RESPONSE_MODE': config.get('response_mode', 'streaming')
            }
            temp_config['LOGGING'] = {
                'LOG_LEVEL': 'INFO',
                'LOG_FILE': ''
            }
            temp_config['OUTPUT'] = {
                'OUTPUT_DIR': '',
                'INCLUDE_TIMESTAMP': 'false'
            }
            temp_config.write(f)
            temp_config_path = f.name
        
        # 初始化执行工具
        config_manager = legacy_wrapper.create_config_manager(temp_config_path)
        excel_handler = legacy_wrapper.create_excel_handler()
        conversation_manager = legacy_wrapper.create_conversation_manager()
        
        # 创建 Dify 客户端
        api_config: Dict[str, Any] = config_manager.get_api_config()  # type: ignore
        response_mode: str = config_manager.get_response_mode()  # type: ignore
        
        # 动态导入 DifyClient
        import sys
        from pathlib import Path
        src_path = Path(__file__).parent.parent.parent.parent / "src"
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        
        from dify_client import DifyClient  # type: ignore
        dify_client = DifyClient(
            api_url=api_config['url'],
            api_key=api_config['key'],
            timeout=api_config['timeout'],
            response_mode=response_mode
        )
        
        add_log("info", "执行引擎初始化完成")
        
        # 执行测试用例
        for i, test_case in enumerate(test_cases):
            # 检查是否需要暂停或停止
            while execution_state["status"] == "paused":
                await asyncio.sleep(1)
            
            if execution_state["status"] == "stopped":
                add_log("warning", "测试被用户停止")
                break
            
            # 更新当前执行的用例
            case_id = test_case.get("id", f"test_case_{i+1}")
            execution_state["progress"]["current"] = case_id
            execution_state["current_response"] = ""
            
            question = test_case.get('user_question', '')
            conversation_group_id = test_case.get('conversation_id', '')
            
            add_log("info", f"执行用例 {i+1}/{len(test_cases)}: {question[:50]}...")
            
            # 准备结果记录
            result = {
                'task_id': task_id,
                'case_id': case_id,
                'conversation_id': conversation_group_id,
                'turn_number': test_case.get('round', 1),
                'user_question': question,
                'expected_response': test_case.get('expected_response', ''),
                'chatflow_reply': '',
                'response_time': 0,
                'api_status': 'failed',
                'error_details': '',
                'call_time': datetime.now().isoformat()
            }
            
            try:
                # 获取或创建会话ID
                conversation_id = conversation_manager.get_conversation_id(conversation_group_id)  # type: ignore
                
                # 记录开始时间
                start_time = time.time()
                
                # 调用 Dify API（带重试机制）
                max_retries = 3
                retry_delay = 2  # 秒
                api_response = None
                response_time = 0
                last_error = None
                
                for attempt in range(max_retries):
                    try:
                        # 检查是否被停止
                        if execution_state["status"] == "stopped":
                            break
                            
                        api_response, response_time = dify_client.send_chat_message(
                            query=question,
                            user_id=api_config.get('user_id', 'test_user'),
                            conversation_id=conversation_id if conversation_id != 'new' else None,
                            inputs=json.loads(test_case.get('inputs', '{}')) if test_case.get('inputs') else {}
                        )
                        break  # 成功则跳出重试循环
                        
                    except Exception as e:
                        last_error = e
                        if attempt < max_retries - 1:
                            add_log("warning", f"API调用失败，等待{retry_delay}秒后重试... (尝试 {attempt + 1}/{max_retries})，错误: {str(e)}")
                            await asyncio.sleep(retry_delay)
                        else:
                            # 最后一次尝试失败
                            raise last_error
                
                # 记录响应时间
                result['response_time'] = round(response_time, 3)
                response_times.append(response_time)
                
                if api_response and execution_state["status"] != "stopped":
                    # 提取答案
                    chatflow_reply = dify_client.extract_answer(api_response)
                    result['chatflow_reply'] = chatflow_reply
                    execution_state["current_response"] = chatflow_reply[:200] + "..." if len(chatflow_reply) > 200 else chatflow_reply
                    
                    # 更新会话ID
                    new_conversation_id = dify_client.extract_conversation_id(api_response)
                    if new_conversation_id:
                        conversation_manager.set_conversation_id(conversation_group_id, new_conversation_id)  # type: ignore
                    
                    result['api_status'] = 'success'
                    execution_state["progress"]["success"] += 1
                    add_log("success", f"用例 {i+1} 执行成功 (响应时间: {response_time:.2f}s)")
                    
                else:
                    result['error_details'] = '未收到有效的API响应或测试被停止'
                    execution_state["progress"]["failed"] += 1
                    add_log("error", f"用例 {i+1} 执行失败: 未收到有效响应")
                    
            except Exception as e:
                result['error_details'] = str(e)
                execution_state["progress"]["failed"] += 1
                add_log("error", f"用例 {i+1} 执行失败: {str(e)}")
            
            # 保存结果
            results.append(result)
            
            # 更新进度
            execution_state["progress"]["completed"] += 1
            
            # 更新统计信息
            if response_times:
                execution_state["statistics"].update({
                    "avg_response_time": sum(response_times) / len(response_times),
                    "min_response_time": min(response_times),
                    "max_response_time": max(response_times),
                    "success_rate": (execution_state["progress"]["success"] / 
                                   execution_state["progress"]["completed"]) * 100
                })
            
            # 测试用例间延迟（避免API冲突）
            if i < len(test_cases) - 1 and execution_state["status"] != "stopped":
                await asyncio.sleep(2)
        
        # 保存测试记录到历史
        test_record = {
            'task_id': task_id,
            'config_name': config['name'],
            'status': execution_state["status"],
            'progress': execution_state["progress"].copy(),
            'statistics': execution_state["statistics"].copy(),
            'start_time': execution_state["start_time"],
            'end_time': execution_state.get("end_time"),
            'results': results
        }
        storage.add_test_record(test_record)
        
        # 测试完成
        if execution_state["status"] == "running":
            execution_state["status"] = "completed"
            execution_state["end_time"] = datetime.now().isoformat()
            success_count = execution_state["progress"]["success"]
            failed_count = execution_state["progress"]["failed"]
            add_log("success", f"测试完成！成功 {success_count} 条，失败 {failed_count} 条")
        
        # 更新测试记录的结束状态
        test_record['status'] = execution_state["status"]
        test_record['end_time'] = execution_state.get("end_time")
        
    except Exception as e:
        execution_state["status"] = "error"
        execution_state["end_time"] = datetime.now().isoformat()
        add_log("error", f"测试执行出错: {str(e)}")
        
        # 保存错误记录
        error_record = {
            'task_id': task_id,
            'config_name': config.get('name', 'unknown'),
            'status': 'error',
            'progress': execution_state["progress"].copy(),
            'start_time': execution_state["start_time"],
            'end_time': execution_state["end_time"],
            'error_message': str(e),
            'results': results
        }
        storage.add_test_record(error_record)
        
    finally:
        # 清理临时配置文件
        temp_config_path = locals().get('temp_config_path')
        if temp_config_path and os.path.exists(temp_config_path):
            try:
                os.unlink(temp_config_path)
            except:
                pass