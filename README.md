# Dify ChatFlow Batch Tool 🚀

**尚书·吏部侍郎** 钦定版 | **贞观二十三年** 九月十四日制

---

## 📜 圣旨

> **朕闻**：天下治乱，在于政通人和；程序优劣，在于测试精良。今有Dify ChatFlow应用，需批量验证其功能完备性。特诏制此工具，以饬天下开发者。

**一个专为 Dify ChatFlow 应用设计的自动化测试工具，提供命令行和Web界面两种使用方式。**

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8%2B-blue.svg)](https://www.typescriptlang.org/)
[![React](https://img.shields.io/badge/React-19.1%2B-61dafb.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![维护状态](https://img.shields.io/badge/维护状态-活跃-brightgreen.svg)](README.md)

## 🏗️ 项目架构

本项目采用**双模块架构**设计，提供两种使用方式：

```
dify_chatflow_batch/
├── src/                     # 🔧 命令行工具模块
│   ├── main.py             # CLI主程序入口
│   ├── config_manager.py   # 配置管理
│   ├── dify_client.py      # Dify API客户端
│   ├── excel_handler.py    # Excel文件处理
│   ├── conversation_manager.py  # 会话管理
│   ├── logger.py           # 日志记录
│   └── README-src.md       # 📖 命令行工具说明
├── web/                     # 🌐 Web界面模块
│   ├── backend/            # FastAPI后端服务
│   ├── frontend/           # React + TypeScript前端
│   ├── data/               # 数据存储目录
│   ├── start.py            # Web启动脚本
│   ├── requirements-web.txt
│   └── README-web.md       # 📖 Web界面说明
├── examples/               # 📋 示例文件
├── requirements.txt        # 核心依赖
└── README.md              # 📖 项目总说明（本文档）
```

## ⭐ 核心特性

### 🎯 通用功能（两个模块共享）
- 🚀 **批量测试执行**: 从Excel文件读取测试用例，如军令传达，批量执行测试
- 💬 **多轮对话支持**: 自动管理conversation_id，如朝堂问答，支持连续多轮对话测试  
- 🌐 **中文字段支持**: 完全支持中文字段名，如汉唐文化，无编码问题
- ⚡ **实时结果写入**: 每完成一个测试用例立即写入结果，如御史记录，避免数据丢失
- 🔄 **智能重试机制**: 所有类型的API错误自动重试3次，如不屈不挠之精神
- 📊 **性能监控**: 记录API响应时间和执行统计，如御史监察
- 📝 **详细日志**: 完善的错误处理和日志记录

## 🏮 使用方式

### 🎯 环境要求
- **Python**: 3.7+ （如文人必备之笔墨）
- **Node.js**: 16+ （仅Web界面需要）
- **操作系统**: Windows 10/11, macOS, Linux （如京师之地）
- **API权限**: 有效的Dify API访问权限 （如入宫之印信）

### 📋 选择使用方式

#### 🔧 方式一：命令行工具（推荐用于自动化）
**适用场景**: CI/CD集成、批量处理、服务器环境、脚本自动化

```bash
# 快速开始
cd src/
# 详细说明请查看: src/README-src.md
```

**特点**: 轻量级、高性能、无GUI依赖、易于集成

#### 🌐 方式二：Web界面（推荐用于交互使用）
**适用场景**: 可视化管理、团队协作、实时监控、配置管理

```bash
# 快速开始
cd web/
# 详细说明请查看: web/README-web.md
```

**特点**: 可视化界面、实时监控、多配置管理、安全加密

## 📋 测试用例格式（如科举考试规范）

### Excel 文件要求
必需列（如科举必考科目）：

| 字段名 | 说明 | 示例 |
|--------|------|------|
| conversation_group_id | 对话组ID | "conv_001" |
| turn_number | 轮次编号（从1开始） | 1, 2, 3... |
| user_question | 用户问题 | "你好" |
| expected_reply | 期望回复（可选） | "您好！" |
| inputs | 额外参数（JSON格式） | "{}" |

### 示例数据
```
conversation_group_id | turn_number | user_question | expected_reply
conv_001             | 1           | 你好          | 问候回复
conv_001             | 2           | 你能做什么？  | 功能介绍
```

## 🔧 配置文件（如律法条文）

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

## 📊 使用场景对比

| 场景特征 | 🔧 命令行工具 | 🌐 Web界面 |
|---------|-------------|----------|
| **自动化集成** | ✅ 完美适配 | ❌ 不适合 |
| **CI/CD流水线** | ✅ 原生支持 | ❌ 复杂 |
| **大量数据处理** | ✅ 无限制 | ⚡ 建议<1000条 |
| **服务器部署** | ✅ 轻量简单 | ⚡ 需要更多资源 |
| **交互式操作** | ❌ 命令行界面 | ✅ 现代化UI |
| **团队协作** | ❌ 需要共享文件 | ✅ 网页访问 |
| **实时监控** | ⚡ 基础日志 | ✅ 丰富图表 |
| **配置管理** | ⚡ 文本编辑 | ✅ 可视化界面 |
| **学习成本** | ⚡ 需要命令行知识 | ✅ 直观易用 |
| **资源占用** | ✅ 极轻量 | ⚡ 中等 |

## 🛠️ 开发和贡献

### 开发环境搭建
```bash
# 克隆项目
git clone <repository-url>
cd dify_chatflow_batch

# 安装核心依赖
pip install -r requirements.txt

# 安装Web依赖（如需开发Web界面）
pip install -r web/requirements-web.txt
cd web/frontend && npm install
```

### 代码结构
- **src/**: 独立的命令行工具，核心业务逻辑
- **web/backend/**: FastAPI后端，封装src模块功能
- **web/frontend/**: React前端，提供现代化UI
- **examples/**: 示例文件和使用案例

## 📜 技术架构

### 核心技术栈
- **命令行工具**: Python 3.7+ 纯净实现
- **Web后端**: FastAPI + Pydantic + Uvicorn
- **Web前端**: React 18 + TypeScript + Ant Design 5.x
- **通信协议**: RESTful API + Server-Sent Events (SSE)
- **数据存储**: 本地文件存储，无数据库依赖
- **安全特性**: API密钥加密存储

### 架构设计原则
- **模块独立**: 命令行工具和Web界面完全独立运行
- **代码复用**: Web后端复用命令行工具的核心逻辑
- **配置兼容**: 两个模块共享相同的配置格式
- **数据一致**: 统一的测试用例格式和结果输出

## 🏆 版本历史

- **v1.2.0** (2025-09-14): 双模块架构完善
  - ✅ 命令行工具模块独立完善
  - ✅ Web界面模块功能完整
  - ✅ 统一的配置和数据格式
  - ✅ 完整的文档体系
  - ✅ 双模块性能优化

- **v1.0.0**: 核心功能发布
  - ✅ 批量测试执行
  - ✅ 多轮对话支持
  - ✅ 智能重试机制
  - ✅ Excel结果导出
  - ✅ 基础Web界面

## 📖 详细文档

根据您的使用需求，请查看对应的详细文档：

- **📖 [命令行工具详细说明](src/README-src.md)** - 适合自动化、CI/CD集成
- **📖 [Web界面详细说明](web/README-web.md)** - 适合交互式使用、团队协作

## 🎖️ 致谢

感谢所有为此项目贡献代码和建议的开发者们。如朝堂群贤毕至，共襄盛举。

## 📞 技术支持

- **通用问题**: 查看对应模块的README文档
- **Bug反馈**: 提交Issue时请说明使用的模块（命令行/Web）
- **功能建议**: 欢迎提出改进建议和新功能需求

## 🎯 选择建议

**🔧 选择命令行工具，如果您：**
- 需要集成到自动化流程
- 处理大量测试数据
- 在服务器环境中运行
- 偏好轻量级解决方案

**🌐 选择Web界面，如果您：**
- 需要可视化操作界面
- 团队协作使用
- 偏好现代化用户体验
- 需要实时监控功能

---

**敕令**：此工具当为天下开发者所用，务必精益求精。

**钤印**：吏部侍郎之印 🏮

**制于**：贞观二十三年九月十四日（公元2025年9月14日）、

**联系我**：![微信公众号](https://wenhua-image.oss-cn-beijing.aliyuncs.com/%E5%BE%AE%E4%BF%A1%E5%85%AC%E4%BC%97%E5%8F%B7/wechat.jpg)

**博客**：[个人博客](https://www.qianshu.wang/)