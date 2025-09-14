# Dify ChatFlow Batch Tool - 命令行工具模块

**高性能批量测试执行引擎** - 专为自动化、CI/CD集成和大数据量处理设计

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://www.python.org/)
[![CLI](https://img.shields.io/badge/Interface-Command%20Line-green.svg)](https://en.wikipedia.org/wiki/Command-line_interface)
[![Performance](https://img.shields.io/badge/Performance-High-brightgreen.svg)](README-src.md)

> **注意**: 这是命令行工具模块的说明文档。如需了解整个项目概览，请查看 [../README.md](../README.md)。

## 🎯 适用场景

### ✅ 强烈推荐使用
- **CI/CD流水线集成** - 无头环境，完美集成
- **大批量数据处理** - 支持数千条测试用例
- **服务器环境部署** - 轻量级，资源占用极低
- **自动化脚本调用** - 标准输入输出，易于集成
- **定时任务执行** - cron/task scheduler 完美支持

### ⚡ 性能优势
- **内存占用**: 仅20-50MB
- **启动速度**: <1秒
- **处理能力**: 无数据量限制
- **并发支持**: 顺序执行，稳定可靠

## 🚀 快速开始

### 📋 环境要求
- **Python**: 3.7+
- **操作系统**: Windows, macOS, Linux
- **依赖**: 标准Python库 + pandas + requests
- **权限**: 读写文件权限

### ⚡ 一键安装和运行

```bash
# 1. 进入命令行工具目录
cd src/

# 2. 安装依赖
pip install -r ../requirements.txt

# 3. 配置API（首次使用）
cp ../config.ini.template ../config.ini
# 编辑 config.ini 填写您的 Dify API 信息

# 4. 运行测试
python main.py ../examples/sample_test_cases.xlsx
```

### 🔧 配置文件设置

编辑项目根目录的 `config.ini` 文件：

```ini
[API]
API_URL = https://api.dify.ai/v1/chat-messages
API_KEY = your-api-key-here
USER_ID = test_user
TIMEOUT = 30
RESPONSE_MODE = streaming

[LOGGING]
LOG_LEVEL = INFO
LOG_FILE = logs/chatflow_test.log

[OUTPUT]
OUTPUT_DIR = results
INCLUDE_TIMESTAMP = true
```

## 📊 命令行选项

### 基础使用
```bash
python main.py <测试用例文件.xlsx>
```

### 高级选项
```bash
python main.py [选项] <测试用例文件>

必需参数:
  test_file                 Excel测试用例文件路径

可选参数:
  -h, --help               显示帮助信息并退出
  -c CONFIG, --config CONFIG
                          指定配置文件路径 (默认: ../config.ini)
  -o OUTPUT, --output OUTPUT
                          指定输出目录 (默认: 配置文件中的设置)
  -v, --verbose           启用详细日志输出
  -q, --quiet            静默模式，仅输出错误信息
  --dry-run              预演模式，不实际调用API
  --max-retries N        设置最大重试次数 (默认: 3)
  --retry-delay N        设置重试间隔秒数 (默认: 5)
```

### 使用示例
```bash
# 基础用例执行
python main.py test_cases.xlsx

# 指定输出目录
python main.py test_cases.xlsx -o ./my_results/

# 详细日志模式
python main.py test_cases.xlsx -v

# 预演模式（不实际调用API）
python main.py test_cases.xlsx --dry-run

# 自定义配置文件
python main.py test_cases.xlsx -c ./my_config.ini
```

## 📋 测试用例格式

### Excel文件要求
- **文件格式**: .xlsx (Excel 2007+)
- **编码**: UTF-8
- **工作表**: 使用第一个工作表

### 必需列
| 列名 | 类型 | 说明 | 示例 |
|------|------|------|------|
| conversation_group_id | 文本 | 对话组标识符 | "conv_001" |
| turn_number | 数字 | 对话轮次(从1开始) | 1, 2, 3... |
| user_question | 文本 | 用户输入问题 | "你好，请介绍一下你自己" |
| expected_reply | 文本 | 期望回复(可选) | "您好！我是AI助手" |
| inputs | JSON | 额外参数(可选) | "{\"key\": \"value\"}" |

### 数据规则
1. **对话连续性**: 同一conversation_group_id内，turn_number必须从1开始连续递增
2. **字符编码**: 支持中文、英文及特殊字符
3. **数据完整性**: conversation_group_id、turn_number、user_question为必填项

### 示例数据
```
conversation_group_id | turn_number | user_question        | expected_reply | inputs
conv_001             | 1           | 你好                  | 问候回复        | {}
conv_001             | 2           | 你能做什么？          | 功能介绍        | {}
conv_002             | 1           | 开始新的对话          | 欢迎信息        | {"context": "new"}
conv_002             | 2           | 继续上面的对话        | 继续回复        | {}
```

## 📤 结果输出

### 输出文件
测试完成后会生成Excel结果文件：
```
结果文件命名: chatflow_test_result_YYYYMMDD_HHMMSS.xlsx
存储路径: 配置文件中指定的OUTPUT_DIR目录
```

### 输出内容
结果文件包含以下列：
- **原始列**: 所有输入的测试用例列
- **chatflow_reply**: Dify API的实际回复
- **response_time**: API响应时间(秒)
- **api_status**: 执行状态(success/failed)
- **error_details**: 错误详情(如有)
- **call_time**: 执行时间戳

### 控制台输出
```
开始测试... 总用例数: 10
[1/10] conv_001-1: 你好 -> 成功 (0.85s)
[2/10] conv_001-2: 你能做什么？ -> 成功 (1.23s)
[3/10] conv_002-1: 开始新对话 -> 失败 (重试中...)
[3/10] conv_002-1: 开始新对话 -> 成功 (0.94s)
...
测试完成! 成功: 9, 失败: 1, 总耗时: 15.67s
结果已保存至: results/chatflow_test_result_20250914_143025.xlsx
```

## 🛠️ 核心模块架构

### 模块说明
```
src/
├── main.py                 # 主程序入口，命令行解析
├── config_manager.py       # 配置文件管理和验证
├── excel_handler.py        # Excel文件读写处理
├── dify_client.py          # Dify API客户端封装
├── conversation_manager.py # 多轮对话状态管理
└── logger.py              # 日志记录和性能监控
```

### 关键特性
- **模块解耦**: 各模块职责明确，便于维护
- **错误处理**: 完善的异常捕获和错误恢复
- **性能优化**: 内存高效使用，适合大数据量
- **日志系统**: 分级日志，支持文件和控制台输出

## 🔄 高级功能

### 智能重试机制
- **自动重试**: 网络错误、超时等自动重试
- **重试策略**: 指数退避算法，避免频繁请求
- **错误分类**: 区分可重试和不可重试错误
- **重试日志**: 详细记录每次重试的原因和结果

### 多轮对话管理
- **会话保持**: 自动管理conversation_id确保对话连续性
- **状态跟踪**: 实时跟踪每个对话组的执行状态
- **异常恢复**: 对话中断时的自动恢复机制

### 性能监控
- **响应时间**: 记录每个API调用的详细时间
- **吞吐量统计**: 计算每秒处理的测试用例数
- **成功率分析**: 实时计算和展示成功率
- **资源监控**: 内存和CPU使用情况跟踪

## 🚨 故障排除

### 常见问题

#### 1. 配置文件问题
```bash
# 问题: FileNotFoundError: config.ini not found
# 解决: 复制配置模板
cp ../config.ini.template ../config.ini
```

#### 2. API连接失败
```bash
# 问题: ConnectionError 或 401 Unauthorized
# 检查项:
# - API_URL 是否正确
# - API_KEY 是否有效
# - 网络连接是否正常
# - 防火墙设置
```

#### 3. Excel文件格式错误
```bash
# 问题: 无法读取Excel文件
# 解决方案:
# - 确保文件是.xlsx格式
# - 检查必需列是否存在
# - 确认数据编码为UTF-8
# - 检查文件是否被占用
```

#### 4. 内存不足
```bash
# 问题: 处理大文件时内存不足
# 解决方案:
# - 分批处理大文件
# - 增加系统虚拟内存
# - 使用64位Python环境
```

### 调试方法

#### 启用详细日志
```bash
python main.py test_cases.xlsx -v
```

#### 预演模式调试
```bash
python main.py test_cases.xlsx --dry-run
```

#### 查看日志文件
```bash
# 日志文件位置在配置文件中指定
tail -f logs/chatflow_test.log
```

## 📈 性能优化

### 推荐配置
```ini
[API]
TIMEOUT = 30          # 根据API响应速度调整
RESPONSE_MODE = streaming  # 流式响应更快

[LOGGING]
LOG_LEVEL = INFO      # 生产环境建议INFO级别

[OUTPUT]
INCLUDE_TIMESTAMP = true  # 便于结果追踪
```

### 批量处理技巧
- **分批执行**: 大量数据分成多个小文件
- **并行处理**: 使用多个进程同时处理不同文件
- **监控资源**: 注意内存和磁盘空间使用
- **定期清理**: 清理临时文件和旧日志

## 🔗 集成示例

### CI/CD集成 (GitHub Actions)
```yaml
name: API Testing
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run tests
      run: |
        cd src
        python main.py ../test_cases/api_tests.xlsx
```

### Docker容器化
```dockerfile
FROM python:3.8-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ ./src/
COPY config.ini .
CMD ["python", "src/main.py", "test_cases.xlsx"]
```

### 定时任务 (Linux Cron)
```bash
# 每天凌晨2点执行API测试
0 2 * * * cd /path/to/project/src && python main.py daily_tests.xlsx
```

---

## 📞 技术支持

### 获取帮助
```bash
python main.py --help
```

### 问题反馈
提交Issue时请包含：
- Python版本
- 操作系统信息
- 完整错误信息
- 测试用例样本(脱敏后)
- 配置文件内容(隐藏敏感信息)

### 日志分析
查看详细日志文件以获取更多调试信息：
```bash
# 实时查看日志
tail -f logs/chatflow_test.log

# 搜索错误信息
grep "ERROR" logs/chatflow_test.log
```

---

**专注于性能、稳定性和易用性 - 命令行工具，您的自动化测试最佳选择！**