# Dify ChatFlow Batch Tool - Web界面模块

**可视化测试管理和执行平台** - 为 Dify ChatFlow 自动化测试工具提供现代化的Web界面

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.1%2B-61dafb.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8%2B-blue.svg)](https://www.typescriptlang.org/)
[![Ant Design](https://img.shields.io/badge/Ant%20Design-5.x-1890ff.svg)](https://ant.design/)

> **注意**: 这是 Web界面模块的说明文档。如需了解整个项目概览，请查看 [../README.md](../README.md)。

## 🌐 Web模块特性

### 🎨 独有优势
- 🎛️ **可视化配置管理**: 图形界面创建和管理多套API配置
- 📁 **拖拽上传**: 支持拖拽上传Excel测试用例文件
- ⚡ **实时执行监控**: 实时显示测试进度和状态
- 📈 **图表化结果**: 美观的测试结果图表展示
- 🔐 **安全加密存储**: API密钥自动加密，界面显示时进行遮蔽
- 👥 **多配置管理**: 支持多套API配置的快速切换
- 🌍 **跨平台访问**: 通过浏览器在任意设备上访问
- 📊 **一键导出**: 测试结果一键导出Excel报告

### 🛠️ 技术架构
- **后端**: FastAPI + Pydantic + Uvicorn
- **前端**: React 18 + TypeScript + Ant Design 5.x
- **实时通信**: Server-Sent Events (SSE)
- **数据存储**: 本地文件系统，无数据库依赖
- **安全特性**: AES加密 + 机器绑定

## 🚀 快速开始

### ⚙️ 环境要求
- **Python**: 3.7+
- **Node.js**: 16+ (前端开发需要)
- **浏览器**: Chrome 90+, Firefox 88+, Safari 14+
- **操作系统**: Windows 10/11, macOS 10.15+, Ubuntu 18+

### 📍 一键启动（推荐）

```bash
# 1. 进入Web模块目录
cd web/

# 2. 安装依赖
pip install -r requirements-web.txt

# 3. 构建前端（仅首次需要）
npm --prefix "./frontend" run build

# 4. 启动Web服务
python start.py

# 5. 访问界面
# 会自动打开浏览器在: http://127.0.0.1:8080
```

### 🔗 访问地址
启动后可访问以下地址：

- **🌐 Web主界面**: http://127.0.0.1:8080
- **📚 API文档**: http://127.0.0.1:8080/docs  
- **🔍 健康检查**: http://127.0.0.1:8080/api/health
- **📡 API基地址**: http://127.0.0.1:8080/api

## 🎨 功能模块

### 🔧 配置管理
- ✅ **多配置支持**: 创建和管理多套API配置  
- ✅ **可视化编辑**: 表单式配置编辑，无需手动编辑ini文件
- ✅ **配置导入**: 自动导入现有config.ini文件
- ✅ **配置备份**: 配置文件的导入/导出功能
- ✅ **实时验证**: API连接测试和配置验证

### 📁 测试用例管理
- ✅ **拖拽上传**: 直接拖拽Excel文件到浏览器
- ✅ **在线预览**: 上传后立即预览测试用例
- ✅ **数据验证**: 自动检查测试用例的格式和完整性
- ✅ **在线编辑**: 支持对测试用例进行简单编辑
- ✅ **批量操作**: 支持选择性执行测试用例

### ⚡ 测试执行引擎
- ✅ **实时执行**: 点击即可开始测试，实时显示进度
- ✅ **执行控制**: 支持暂停、恢复、停止操作
- ✅ **并发执行**: 可设置并发数控制执行速度
- ✅ **错误处理**: 自动重试和错误恢复机制
- ✅ **进度追踪**: 实时进度条和详细状态信息

### 📈 结果展示和分析
- ✅ **实时结果**: 测试进行中实时显示结果
- ✅ **统计图表**: 成功率、响应时间等关键指标图表
- ✅ **结果筛选**: 按状态、时间等条件筛选结果
- ✅ **详细日志**: 每个测试用例的详细执行日志
- ✅ **结果导出**: 一键导出Excel测试报告

## 📂 项目目录结构

```
web/
├── backend/                    # 后端API
│   ├── main.py                # FastAPI应用入口
│   ├── storage.py             # 文件存储管理
│   ├── security.py            # API密钥加密
│   ├── models/
│   │   └── schemas.py         # 数据模型定义
│   ├── routes/
│   │   └── execution.py       # 执行相关API
│   └── services/
│       └── legacy_wrapper.py  # 命令行工具封装
├── frontend/                   # 前端React应用
│   ├── src/
│   │   ├── components/        # React组件
│   │   ├── pages/            # 页面组件
│   │   ├── services/         # API服务
│   │   └── types/            # TypeScript类型定义
│   ├── package.json
│   └── vite.config.ts
├── data/                       # 数据存储目录
│   ├── configs/               # 配置文件(.ini)
│   ├── test_cases.json        # 测试用例
│   ├── test_history.json      # 测试历史
│   └── settings.json          # 系统设置
├── requirements-web.txt        # Python依赖
├── start.py                   # 启动脚本
└── README-web.md              # 本文档
```

## 🛠️ 开发说明

### 后端开发
```bash
# 直接运行后端（开发模式）
cd backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8080
```

### 前端开发
```bash
# 直接运行前端（开发模式）
cd frontend
npm install
npm run dev
```

### 生产构建
```bash
# 构建前端
cd frontend
npm run build

# 构建后的文件输出到 frontend/dist/
# 可通过后端静态文件服务访问
```

## 📊 数据存储

### 配置文件管理
- **位置**: `data/configs/*.ini`
- **格式**: 与命令行工具完全兼容
- **加密**: API密钥自动加密存储
- **导入**: 首次启动自动导入根目录的 `config.ini`

### 测试数据管理
- **测试用例**: `data/test_cases.json` (JSON数组格式)
- **测试历史**: `data/test_history.json` (自动保留最近100条记录)
- **系统设置**: `data/settings.json` (活跃配置、UI偏好等)

### 安全特性
- **API密钥加密**: 使用 `cryptography` 库进行AES加密
- **机器绑定**: 密钥与机器信息绑定，增强安全性
- **界面遮蔽**: 密钥在界面显示时自动部分遮蔽
- **本地存储**: 所有敏感数据仅在本地存储

## 📈 性能特性

### 资源占用
- **内存使用**: 约100-200MB
- **启动时间**: 3-5秒
- **并发支持**: 支持多用户同时访问
- **数据处理**: 建议单次处理<1000条测试用例

### 优化建议
- **浏览器缓存**: 利用浏览器缓存提升加载速度
- **分批处理**: 大量数据分批执行避免界面卡顿
- **定期清理**: 清理历史数据和临时文件
- **网络优化**: 本地部署获得最佳性能

## 🚨 故障排除

### 常见问题

#### 1. 端口占用
```bash
# 问题: 默认端口8080被占用
# 解决: 修改 start.py 中的端口设置
# 或使用命令行参数指定端口
```

#### 2. 前端构建失败
```bash
# 问题: npm run build 失败
# 解决方案:
cd frontend
rm -rf node_modules
npm install
npm run build
```

#### 3. 后端依赖问题
```bash
# 重新安装Python依赖
pip install -r requirements-web.txt --force-reinstall
```

#### 4. 浏览器无法访问
```bash
# 检查防火墙设置
# 确认服务启动成功
# 尝试使用 127.0.0.1 而不是 localhost
```

#### 5. 数据重置
```bash
# 删除数据目录重新初始化
rm -rf data/
python start.py
```

### 调试方法

#### 查看后端日志
```bash
# 启动脚本会显示详细的启动日志
python start.py
```

#### 查看前端日志
```bash
# 在浏览器开发者工具中查看控制台输出
# F12 -> Console
```

#### API调试
```bash
# 访问API文档进行接口测试
http://127.0.0.1:8080/docs
```

### 开发环境调试
```bash
# 同时启动前后端开发服务
# 终端1: 启动后端
cd backend && python -m uvicorn main:app --reload

# 终端2: 启动前端
cd frontend && npm run dev

# 前端会在 http://localhost:3000
# 后端会在 http://127.0.0.1:8080
```

## 🔧 自定义配置

### 修改默认端口
编辑 `start.py` 文件：
```python
# 修改后端端口
manager.start_backend(port=8081)

# 修改前端端口（开发模式）
manager.start_frontend(port=3001)
```

### 修改数据目录
```python
# 在 start.py 中修改数据目录路径
self.data_dir = Path("/custom/data/path")
```

### 自定义前端构建
```bash
# 修改 frontend/vite.config.ts
export default defineConfig({
  base: '/custom-path/',  # 自定义基础路径
  build: {
    outDir: 'custom-dist'  # 自定义输出目录
  }
})
```

## 📞 技术支持

### 获取帮助
- **Web界面**: 查看界面上的帮助提示
- **API文档**: http://127.0.0.1:8080/docs
- **健康检查**: http://127.0.0.1:8080/api/health

### 问题反馈
提交Issue时请包含：
- 浏览器版本和类型
- 操作系统信息
- 完整错误信息和截图
- 网络环境描述
- 复现步骤

### 日志收集
```bash
# 后端日志：启动脚本的控制台输出
# 前端日志：浏览器开发者工具控制台
# 系统日志：检查系统事件日志
```

---

**现代化、直观、强大 - 让测试管理变得简单高效！**