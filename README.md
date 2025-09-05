# Chatflow 自动化测试工具

一个专为 Dify Chatflow 应用设计的自动化测试工具，支持批量测试用例执行、多轮对话管理和详细的测试结果记录。

## 🚀 功能特性

- **批量测试执行**: 从 Excel 文件读取测试用例，批量执行测试
- **多轮对话支持**: 自动管理 conversation_id，支持连续的多轮对话测试
- **中文字段支持**: 完全支持中文字段名（对话ID、轮次、用户问题、期待回复）
- **实时结果写入**: 每完成一个测试用例立即写入结果，避免数据丢失
- **智能重试机制**: 所有类型的API错误都会自动重试3次，每次间隔5秒
- **灵活的配置管理**: 通过配置文件管理 API 参数、日志设置等
- **详细的结果记录**: 自动保存测试结果到 Excel 文件，包含响应时间、错误信息等
- **进度显示**: 实时显示测试进度和统计信息
- **错误处理**: 完善的错误处理和日志记录机制
- **性能监控**: 记录 API 响应时间和执行统计

## 📋 系统要求

- Python 3.7 或更高版本
- Windows 10/11（推荐）或其他支持 Python 的操作系统
- 有效的 Dify API 访问权限

## 🛠️ 安装步骤

### 1. 克隆或下载项目

```bash
# 如果使用 Git
git clone <repository-url>
cd chatflow-test-tool

# 或者直接下载并解压项目文件
```

### 2. 安装依赖

```bash
# 安装 Python 依赖包
pip install -r requirements.txt
```

### 3. 配置设置

复制配置模板并填写您的 API 信息：

```bash
# 复制配置模板
copy config.ini.template config.ini
```

编辑 `config.ini` 文件，填写您的 Dify API 信息：

```ini
[API]
url = https://api.dify.ai/v1/chat-messages
key = your-api-key-here
user_id = test_user
timeout = 30

[LOG]
level = INFO
file = logs/chatflow_test.log

[OUTPUT]
directory = results
include_timestamp = true
```

## 📖 使用方法

### 基本用法

```bash
# 使用示例测试用例
python src/main.py examples/sample_test_cases.xlsx

# 指定输出文件名
python src/main.py examples/sample_test_cases.xlsx -o my_results.xlsx

# 使用自定义配置文件
python src/main.py test_cases.xlsx -c my_config.ini
```

### 命令行参数

```
python src/main.py [输入文件] [选项]

位置参数:
  输入文件              测试用例 Excel 文件路径

可选参数:
  -h, --help           显示帮助信息
  -o, --output 文件名   指定输出文件名
  -c, --config 配置文件 指定配置文件路径 (默认: config.ini)
  --version            显示版本信息
```

### 测试用例格式

测试用例必须是 Excel 文件 (.xlsx)，支持中文字段名，包含以下列：

| 列名 | 类型 | 必需 | 说明 |
|------|------|------|------|
| 对话ID | 文本 | 是 | 对话标识符，用于区分不同的对话会话 |
| 轮次 | 数字 | 是 | 对话轮次，从1开始递增 |
| 用户问题 | 文本 | 是 | 要发送给AI的问题 |
| 期待回复 | 文本 | 否 | 期望的回答（用于人工对比） |
| inputs | 文本 | 否 | 额外的输入参数，JSON格式字符串 |
| description | 文本 | 否 | 测试用例的描述信息 |

**注意**: 工具同时支持英文字段名（conversation_id, round, question, expected_answer）和中文字段名，可以混合使用。

### 示例测试用例

```excel
对话ID | 轮次 | 用户问题 | 期待回复 | inputs | description
conv_001 | 1 | 你好，请介绍一下你的功能 | 应该包含功能介绍 | {} | 基础问候测试
conv_002 | 1 | 我想了解车险产品 | 应该提供车险信息 | {"user_type": "个人"} | 车险咨询-第1轮
conv_002 | 2 | 保费怎么计算？ | 应该说明计算方法 | {} | 车险咨询-第2轮
```

## 📁 项目结构

```
chatflow-test-tool/
├── src/                          # 源代码目录
│   ├── __init__.py              # 包初始化文件
│   ├── main.py                  # 主程序入口
│   ├── config_manager.py        # 配置管理模块
│   ├── excel_handler.py         # Excel文件处理模块
│   ├── dify_client.py           # Dify API客户端
│   ├── conversation_manager.py  # 会话管理模块
│   └── logger.py                # 日志和错误处理模块
├── examples/                     # 示例文件目录
│   ├── sample_test_cases.xlsx   # 示例测试用例
│   ├── test_cases_template.xlsx # 测试用例模板
│   ├── sample_test_cases.py     # 示例文件生成器
│   └── README.md                # 示例文件说明
├── results/                      # 测试结果目录（自动创建）
├── logs/                         # 日志文件目录（自动创建）
├── config.ini.template          # 配置文件模板
├── requirements.txt             # Python依赖列表
├── .gitignore                   # Git忽略文件
├── 开发计划.md                   # 项目开发计划
└── README.md                    # 项目说明文档
```

## 🔧 配置说明

### API 配置

```ini
[API]
url = https://api.dify.ai/v1/chat-messages  # Dify API 端点
key = your-api-key-here                     # 您的 API 密钥
user_id = test_user                         # 测试用户ID
timeout = 30                                # 请求超时时间（秒）
```

### 日志配置

```ini
[LOG]
level = INFO                    # 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
file = logs/chatflow_test.log   # 日志文件路径
```

### 输出配置

```ini
[OUTPUT]
directory = results        # 结果文件保存目录
include_timestamp = true   # 是否在文件名中包含时间戳
```

## 📊 测试结果

工具采用**实时写入机制**，每完成一个测试用例就立即保存到 Excel 文件中，确保数据不会因程序中断而丢失。

### 输出文件命名
- 默认格式：`result_YYYYMMDD_HHMMSS.xlsx`
- 自定义文件名：使用 `-o` 参数指定

### 结果文件内容

测试结果文件包含以下信息：

- **输入信息**: 所有原始测试用例数据（支持中文字段名）
- **实际回答**: AI 的实际响应内容
- **响应时间**: API 调用的响应时间（秒）
- **执行状态**: 成功/失败状态
- **错误信息**: 如果失败，记录具体错误
- **时间戳**: 执行时间记录

### 结果分析

您可以通过以下方式分析测试结果：

1. **功能验证**: 对比 `expected_answer` 和 `actual_answer`
2. **性能分析**: 查看 `api_response_time` 列的响应时间
3. **错误排查**: 检查 `status` 和 `error_message` 列
4. **统计分析**: 查看控制台输出的测试总结

## 🚨 常见问题

### Q: 提示 "配置文件不存在" 错误
A: 请确保已经复制 `config.ini.template` 为 `config.ini` 并填写了正确的配置信息。

### Q: API 连接失败
A: 请检查：
- API URL 是否正确
- API Key 是否有效
- 网络连接是否正常
- 防火墙设置是否阻止了连接

### Q: Excel 文件格式错误
A: 请确保：
- 文件是 .xlsx 格式
- 包含所有必需的列（conversation_id, round, question）
- 数据格式正确（round 必须是数字）

### Q: 多轮对话不连续
A: 请检查：
- 相同 conversation_id 的 round 是否从 1 开始连续递增
- 是否有重复的 conversation_id + round 组合

### Q: 中文字符显示异常
A: 请确保：
- Excel 文件使用 UTF-8 编码保存
- 控制台支持中文字符显示
- 工具已完全支持中文字段名（对话ID、轮次、用户问题、期待回复）

### Q: 测试过程中程序中断，结果是否会丢失？
A: 不会丢失。工具采用实时写入机制，每完成一个测试用例就立即保存到Excel文件中，即使程序意外中断，已完成的测试结果也会被保留。

### Q: API调用失败怎么办？
A: 工具内置智能重试机制：
- 所有类型的API错误都会自动重试3次
- 每次重试间隔5秒
- 重试过程会在日志中详细记录

## 🔒 安全注意事项

1. **API 密钥保护**: 
   - 不要将 `config.ini` 文件提交到版本控制系统
   - 定期更换 API 密钥
   - 限制 API 密钥的访问权限

2. **数据安全**:
   - 测试数据可能包含敏感信息，请妥善保管
   - 定期清理测试结果和日志文件
   - 在共享环境中使用时注意数据隔离

## 🤝 贡献指南

欢迎提交问题报告和功能建议！如果您想贡献代码：

1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📝 更新日志

### v1.1.0 (2025-01-XX)
- **新增**: 完全支持中文字段名（对话ID、轮次、用户问题、期待回复）
- **新增**: 实时结果写入机制，每完成一个测试用例立即保存
- **改进**: 智能重试机制，所有API错误自动重试3次，间隔5秒
- **优化**: 输出文件名格式调整为 `result_YYYYMMDD_HHMMSS.xlsx`
- **增强**: 更好的错误处理和日志记录

### v1.0.0 (2024-01-XX)
- 初始版本发布
- 支持批量测试用例执行
- 多轮对话管理
- Excel 文件输入输出
- 配置文件管理
- 日志和错误处理

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持

如果您在使用过程中遇到问题，请：

1. 查看本文档的常见问题部分
2. 检查日志文件中的详细错误信息
3. 提交 Issue 并附上详细的错误信息和复现步骤

---

**开发团队**: AI Assistant  
**最后更新**: 2024年1月  
**版本**: v1.0.0