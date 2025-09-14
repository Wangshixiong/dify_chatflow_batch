"""
FastAPI应用入口
提供Web API服务
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Optional
import uvicorn
import logging
from pathlib import Path

# 导入本地模块
try:
    # 相对导入（作为包运行时）
    from .storage import storage
    from .security import security
    from .services.legacy_wrapper import legacy_wrapper
    from .models.schemas import (
        ConfigCreate, ConfigUpdate, Config, ApiResponse,
        TestCaseCreate, TestCaseUpdate, TestCase, ConnectionTestRequest, ConnectionTestResponse
    )
    from .routes.execution import router as execution_router
except ImportError:
    # 绝对导入（直接运行时）
    from storage import storage
    from security import security
    from services.legacy_wrapper import legacy_wrapper
    from models.schemas import (
        ConfigCreate, ConfigUpdate, Config, ApiResponse,
        TestCaseCreate, TestCaseUpdate, TestCase, ConnectionTestRequest, ConnectionTestResponse
    )
    from routes.execution import router as execution_router

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="Dify ChatFlow Batch Tool API",
    description="Web界面后端API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",    # React开发服务器
        "http://localhost:5173",    # Vite默认端口
        "http://localhost:8080",    # 当前应用端口
        "http://127.0.0.1:8080"     # 本地回环地址
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(execution_router)

# 静态文件服务（前端构建后的文件）
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    # 挂载assets目录到/assets路径
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    # 挂载其他静态文件到根路径
    app.mount("/vite.svg", StaticFiles(directory=frontend_dist), name="static")

# 根路径
@app.get("/")
async def root():
    """根路径，返回前端页面或API信息"""
    frontend_index = frontend_dist / "index.html"
    if frontend_index.exists():
        return FileResponse(frontend_index)
    else:
        return {"message": "Dify ChatFlow Batch Tool API", "docs": "/docs"}

# 健康检查
@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "legacy_modules": legacy_wrapper.available,
        "timestamp": storage.get_settings().get("created_at")
    }

# 配置管理API
@app.get("/api/configs", response_model=ApiResponse)
async def get_configs():
    """获取配置列表"""
    try:
        configs = storage.list_configs()
        
        # 遮蔽API密钥
        for config in configs:
            if 'api_key' in config:
                config['api_key_masked'] = security.mask_api_key(config['api_key'])
                del config['api_key']  # 不返回原始密钥
        
        return ApiResponse(
            success=True,
            message="获取配置列表成功",
            data=configs
        )
    except Exception as e:
        logger.error(f"获取配置列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/configs", response_model=ApiResponse)
async def create_config(config: ConfigCreate):
    """创建新配置"""
    try:
        # 检查配置名是否已存在
        existing_configs = storage.list_configs()
        if any(c['name'] == config.name for c in existing_configs):
            raise HTTPException(status_code=400, detail="配置名称已存在")
        
        # 加密API密钥
        encrypted_key = security.encrypt_api_key(config.api_key)
        
        # 保存配置
        config_data = config.dict()
        config_data['api_key'] = encrypted_key
        
        success = storage.save_config(config.name, config_data)
        if not success:
            raise HTTPException(status_code=500, detail="保存配置失败")
        
        return ApiResponse(
            success=True,
            message="配置创建成功",
            data={"name": config.name}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/configs/{config_name}", response_model=ApiResponse)
async def update_config(config_name: str, config: ConfigUpdate):
    """更新配置"""
    try:
        # 检查配置是否存在
        existing_configs = storage.list_configs()
        existing_config = next((c for c in existing_configs if c['name'] == config_name), None)
        if not existing_config:
            raise HTTPException(status_code=404, detail="配置不存在")
        
        # 准备更新数据
        update_data = {k: v for k, v in config.dict().items() if v is not None}
        
        # 如果更新API密钥，需要加密
        if 'api_key' in update_data:
            update_data['api_key'] = security.encrypt_api_key(update_data['api_key'])
        
        # 合并现有配置
        config_data = existing_config.copy()
        config_data.update(update_data)
        
        success = storage.save_config(config_name, config_data)
        if not success:
            raise HTTPException(status_code=500, detail="更新配置失败")
        
        return ApiResponse(
            success=True,
            message="配置更新成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/configs/{config_name}", response_model=ApiResponse)
async def delete_config(config_name: str):
    """删除配置"""
    try:
        success = storage.delete_config(config_name)
        if not success:
            raise HTTPException(status_code=404, detail="配置不存在或无法删除")
        
        return ApiResponse(
            success=True,
            message="配置删除成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/configs/test", response_model=ConnectionTestResponse)
async def test_connection(request: ConnectionTestRequest):
    """测试API连接"""
    try:
        # 测试连接
        result = legacy_wrapper.test_api_connection(
            api_url=str(request.api_url),
            api_key=request.api_key,
            timeout=request.timeout
        )
        
        return ConnectionTestResponse(**result)
        
    except Exception as e:
        logger.error(f"测试连接失败: {e}")
        return ConnectionTestResponse(
            success=False,
            message=f"测试连接失败: {str(e)}"
        )

@app.post("/api/configs/{config_name}/test", response_model=ConnectionTestResponse)
async def test_config_connection(config_name: str):
    """测试已保存配置的连接"""
    try:
        # 获取配置
        configs = storage.list_configs()
        config = next((c for c in configs if c['name'] == config_name), None)
        if not config:
            raise HTTPException(status_code=404, detail="配置不存在")
        
        # 解密API密钥
        api_key = config.get('api_key') or ''
        decrypted_key = security.decrypt_api_key(api_key)
        
        # 测试连接
        result = legacy_wrapper.test_api_connection(
            api_url=str(config['api_url']),
            api_key=decrypted_key,
            timeout=config.get('timeout', 30)
        )
        
        return ConnectionTestResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试连接失败: {e}")
        return ConnectionTestResponse(
            success=False,
            message=f"测试连接失败: {str(e)}"
        )

@app.post("/api/configs/{config_name}/activate", response_model=ApiResponse)
async def activate_config(config_name: str):
    """激活配置"""
    try:
        # 检查配置是否存在
        configs = storage.list_configs()
        if not any(c['name'] == config_name for c in configs):
            raise HTTPException(status_code=404, detail="配置不存在")
        
        storage.set_active_config(config_name)
        
        return ApiResponse(
            success=True,
            message=f"配置 {config_name} 已激活"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"激活配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/configs/import", response_model=ApiResponse)
async def import_config_from_ini(file: UploadFile = File(...)):
    """从INI文件导入配置"""
    try:
        # 检查文件类型
        if not file.filename or not file.filename.endswith('.ini'):
            raise HTTPException(status_code=400, detail="只支持INI格式文件")
        
        # 保存临时文件
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ini') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # 解析INI文件
            import configparser
            config = configparser.ConfigParser()
            config.read(tmp_path, encoding='utf-8')
            
            # 提取配置数据
            config_data = {}
            if 'API' in config:
                config_data.update({
                    'api_url': config['API'].get('API_URL', ''),
                    'api_key': config['API'].get('API_KEY', ''),
                    'user_id': config['API'].get('USER_ID', 'test_user'),
                    'timeout': int(config['API'].get('TIMEOUT', 120)),
                    'response_mode': config['API'].get('RESPONSE_MODE', 'streaming')
                })
            
            if 'LOGGING' in config:
                config_data.update({
                    'log_level': config['LOGGING'].get('LOG_LEVEL', 'INFO'),
                    'log_file': config['LOGGING'].get('LOG_FILE', '')
                })
            
            if 'OUTPUT' in config:
                config_data.update({
                    'output_dir': config['OUTPUT'].get('OUTPUT_DIR', ''),
                    'include_timestamp': config['OUTPUT'].get('INCLUDE_TIMESTAMP', 'true').lower() == 'true'
                })
            
            # 生成配置名称
            import os
            if not file.filename:
                raise HTTPException(status_code=400, detail="文件名为空")
            config_name = os.path.splitext(file.filename)[0]
            
            # 检查配置名是否已存在
            existing_configs = storage.list_configs()
            counter = 1
            original_name = config_name
            while any(c['name'] == config_name for c in existing_configs):
                config_name = f"{original_name}_{counter}"
                counter += 1
            
            # 加密API密钥
            if config_data.get('api_key'):
                config_data['api_key'] = security.encrypt_api_key(config_data['api_key'])
            
            # 保存配置
            success = storage.save_config(config_name, config_data)
            if not success:
                raise HTTPException(status_code=500, detail="保存配置失败")
            
            return ApiResponse(
                success=True,
                message=f"配置已导入: {config_name}",
                data={"name": config_name}
            )
            
        finally:
            # 清理临时文件
            Path(tmp_path).unlink(missing_ok=True)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导入配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/configs/{config_name}/export")
async def export_config_to_ini(config_name: str):
    """导出配置为INI文件"""
    try:
        # 获取配置
        configs = storage.list_configs()
        config = next((c for c in configs if c['name'] == config_name), None)
        if not config:
            raise HTTPException(status_code=404, detail="配置不存在")
        
        # 解密API密钥
        api_key = config.get('api_key') or ''
        decrypted_key = security.decrypt_api_key(api_key)
        
        # 创建INI文件
        import configparser
        import tempfile
        
        config_parser = configparser.ConfigParser()
        
        config_parser['API'] = {
            'API_URL': config.get('api_url', ''),
            'API_KEY': decrypted_key,
            'USER_ID': config.get('user_id', 'test_user'),
            'TIMEOUT': str(config.get('timeout', 120)),
            'RESPONSE_MODE': config.get('response_mode', 'streaming')
        }
        
        config_parser['LOGGING'] = {
            'LOG_LEVEL': config.get('log_level', 'INFO'),
            'LOG_FILE': config.get('log_file', '')
        }
        
        config_parser['OUTPUT'] = {
            'OUTPUT_DIR': config.get('output_dir', ''),
            'INCLUDE_TIMESTAMP': str(config.get('include_timestamp', True)).lower()
        }
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ini', mode='w', encoding='utf-8') as tmp:
            config_parser.write(tmp)
            tmp_path = tmp.name
        
        return FileResponse(
            tmp_path,
            filename=f"{config_name}.ini",
            media_type="text/plain"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 测试用例管理API
@app.get("/api/testcases", response_model=ApiResponse)
async def get_test_cases():
    """获取测试用例列表"""
    try:
        cases = storage.get_test_cases()
        return ApiResponse(
            success=True,
            message="获取测试用例成功",
            data=cases
        )
    except Exception as e:
        logger.error(f"获取测试用例失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/testcases/upload", response_model=ApiResponse)
async def upload_test_cases(file: UploadFile = File(...)):
    """上传测试用例文件"""
    try:
        # 检查文件类型
        if not file.filename or not file.filename.endswith(('.xlsx', '.xls', '.csv')):
            raise HTTPException(status_code=400, detail="不支持的文件格式")
        
        # 保存临时文件
        import tempfile
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名为空")
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # 解析文件
            result = legacy_wrapper.parse_excel_file(tmp_path)
            
            if result['success']:
                # 保存测试用例
                storage.save_test_cases(result['cases'])
                
                return ApiResponse(
                    success=True,
                    message=f"成功上传 {len(result['cases'])} 条测试用例",
                    data={
                        "filename": file.filename,
                        "size": len(content),
                        "cases_count": len(result['cases'])
                    }
                )
            else:
                raise HTTPException(status_code=400, detail=result['message'])
                
        finally:
            # 清理临时文件
            Path(tmp_path).unlink(missing_ok=True)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/testcases", response_model=ApiResponse)
async def create_test_case(case: TestCaseCreate):
    """创建测试用例"""
    try:
        case_id = storage.add_test_case(case.dict())
        return ApiResponse(
            success=True,
            message="测试用例创建成功",
            data={"id": case_id}
        )
    except Exception as e:
        logger.error(f"创建测试用例失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/testcases/{case_id}", response_model=ApiResponse)
async def update_test_case(case_id: str, case: TestCaseUpdate):
    """更新测试用例"""
    try:
        # 准备更新数据
        update_data = {k: v for k, v in case.dict().items() if v is not None}
        
        success = storage.update_test_case(case_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail="测试用例不存在")
        
        return ApiResponse(
            success=True,
            message="测试用例更新成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新测试用例失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/testcases/{case_id}", response_model=ApiResponse)
async def delete_test_case(case_id: str):
    """删除测试用例"""
    try:
        success = storage.delete_test_case(case_id)
        if not success:
            raise HTTPException(status_code=404, detail="测试用例不存在")
        
        return ApiResponse(
            success=True,
            message="测试用例删除成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除测试用例失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/testcases", response_model=ApiResponse)
async def clear_test_cases():
    """清空所有测试用例"""
    try:
        storage.save_test_cases([])
        return ApiResponse(
            success=True,
            message="测试用例已清空"
        )
    except Exception as e:
        logger.error(f"清空测试用例失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/testcases/template")
async def download_template():
    """下载测试用例模板"""
    try:
        # 创建模板文件
        import tempfile
        import pandas as pd
        
        # 模板数据
        template_data = {
            '对话ID': ['conversation_1', 'conversation_1', 'conversation_2'],
            '轮次': [1, 2, 1],
            '用户问题': ['你好，请介绍一下自己', '你能做什么？', '什么是人工智能？'],
            '期待回复': ['应该包含自我介绍', '应该列出能力清单', '应该解释AI概念'],
            'inputs': ['{}', '{}', '{}']
        }
        
        df = pd.DataFrame(template_data)
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            df.to_excel(tmp.name, index=False, engine='openpyxl')
            tmp_path = tmp.name
        
        return FileResponse(
            tmp_path,
            filename="测试用例模板.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        logger.error(f"生成模板失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 结果管理API
@app.get("/api/results", response_model=ApiResponse)
async def get_results(task_id: Optional[str] = None):
    """获取测试结果列表"""
    try:
        results = storage.get_test_results(task_id)
        return ApiResponse(
            success=True,
            message="获取结果成功",
            data=results
        )
    except Exception as e:
        logger.error(f"获取结果失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/results/{result_id}", response_model=ApiResponse)
async def get_result_detail(result_id: str):
    """获取单个结果详情"""
    try:
        # 从所有结果中查找
        all_results = storage.get_test_results()
        result = next((r for r in all_results if r.get('case_id') == result_id), None)
        
        if not result:
            raise HTTPException(status_code=404, detail="结果不存在")
        
        return ApiResponse(
            success=True,
            message="获取结果详情成功",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取结果详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/results/export")
async def export_results(
    task_id: Optional[str] = None,
    format: str = "excel",
    scope: str = "all"
):
    """导出测试结果"""
    try:
        if format not in ["excel", "csv", "json"]:
            raise HTTPException(status_code=400, detail="不支持的导出格式")
        
        if scope not in ["all", "success", "failed"]:
            raise HTTPException(status_code=400, detail="不支持的导出范围")
        
        export_result = storage.export_results(task_id, format, scope)
        
        if not export_result['success']:
            raise HTTPException(status_code=400, detail=export_result['message'])
        
        # 返回文件下载
        return FileResponse(
            export_result['file_path'],
            filename=export_result['filename'],
            media_type={
                'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'csv': 'text/csv',
                'json': 'application/json'
            }[format]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出结果失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 历史记录管理API
@app.get("/api/history", response_model=ApiResponse)
async def get_test_history():
    """获取测试历史记录"""
    try:
        history = storage.get_test_history()
        # 不返回详细的results，只返回摘要信息
        summary_history = []
        for record in history:
            summary = {
                'id': record.get('id'),
                'task_id': record.get('task_id'),
                'config_name': record.get('config_name'),
                'status': record.get('status'),
                'progress': record.get('progress', {}),
                'statistics': record.get('statistics', {}),
                'start_time': record.get('start_time'),
                'end_time': record.get('end_time'),
                'created_at': record.get('created_at'),
                'results_count': len(record.get('results', []))
            }
            summary_history.append(summary)
        
        return ApiResponse(
            success=True,
            message="获取历史记录成功",
            data=summary_history
        )
    except Exception as e:
        logger.error(f"获取历史记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history/{record_id}", response_model=ApiResponse)
async def get_history_detail(record_id: str):
    """获取历史记录详情"""
    try:
        record = storage.get_test_record(record_id)
        if not record:
            raise HTTPException(status_code=404, detail="历史记录不存在")
        
        return ApiResponse(
            success=True,
            message="获取历史记录详情成功",
            data=record
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取历史记录详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/history/{record_id}", response_model=ApiResponse)
async def delete_history_record(record_id: str):
    """删除历史记录"""
    try:
        success = storage.delete_test_record(record_id)
        if not success:
            raise HTTPException(status_code=404, detail="历史记录不存在或无法删除")
        
        return ApiResponse(
            success=True,
            message="历史记录删除成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除历史记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def start_server(host: str = "127.0.0.1", port: int = 8081):
    """启动服务器"""
    logger.info(f"启动Web服务器: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    start_server()