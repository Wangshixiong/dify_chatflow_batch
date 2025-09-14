# Dify ChatFlow Batch Tool - Web界面开发计划

## 📋 项目概述

基于现有命令行工具，开发Web前端界面，保持原有功能完全可用的前提下，提供可视化的测试管理体验。

## 🎯 开发原则

- **零影响**: 不修改现有 `src/` 目录下任何代码
- **代码复用**: 最大化复用现有Python逻辑
- **保持简单**: 功能优先，避免过度设计
- **独立部署**: Web功能作为可选增强

## 📅 开发计划

### 第一阶段：基础架构搭建 (1-2天)

#### 1.1 后端基础架构
- [ ] 创建 `web/backend/` 目录结构
- [ ] 搭建 FastAPI 应用框架
- [ ] 配置CORS和静态文件服务
- [ ] 设计简单文件存储结构 (`web/data/` 目录)
- [ ] 实现现有模块的导入和封装
- [ ] 创建基础的数据模型 (Pydantic schemas + 严格验证)
- [ ] 实现API密钥加密存储机制

**交付物**:
- `web/backend/main.py` - FastAPI应用入口
- `web/backend/models/schemas.py` - 数据模型定义 (含严格验证)
- `web/backend/storage.py` - 文件存储管理
- `web/backend/security.py` - API密钥加密/解密
- `web/requirements-web.txt` - 后端依赖 (含cryptography)

#### 1.2 前端基础架构
- [ ] 使用 Vite 创建 React + TypeScript 项目
- [ ] 配置 Ant Design 5.x
- [ ] 设置项目目录结构
- [ ] 配置 Axios 和 API 基础服务
- [ ] 创建基础的类型定义

**交付物**:
- `web/frontend/` 完整前端项目结构
- `web/frontend/src/types/index.ts` - TypeScript类型定义
- `web/frontend/src/services/api.ts` - API服务封装

#### 1.3 启动脚本
- [ ] 创建 `web/start.py` 统一启动脚本
- [ ] 实现前端构建和后端启动的自动化
- [ ] 添加端口检测和浏览器自动打开

**交付物**:
- `web/start.py` - 一键启动脚本 (含首次初始化逻辑)
- `web/README-web.md` - Web使用说明
- `web/data/` - 数据目录 (自动创建)

### 第二阶段：核心功能开发 (3-4天)

#### 2.1 配置管理模块
**后端API**:
- [ ] `GET /api/configs` - 获取配置列表
- [ ] `POST /api/configs` - 创建配置
- [ ] `PUT /api/configs/{id}` - 更新配置
- [ ] `DELETE /api/configs/{id}` - 删除配置
- [ ] `POST /api/configs/{id}/test` - 测试连接

**前端组件**:
- [ ] `ConfigPanel.tsx` - 配置管理面板
- [ ] `useConfig.ts` - 配置管理Hook
- [ ] 配置表单验证和错误处理
- [ ] 本地存储集成

#### 2.2 测试用例管理模块
**后端API**:
- [ ] `POST /api/testcases/upload` - 文件上传
- [ ] `GET /api/testcases` - 获取用例列表
- [ ] `POST /api/testcases` - 添加用例
- [ ] `PUT /api/testcases/{id}` - 更新用例
- [ ] `DELETE /api/testcases/{id}` - 删除用例
- [ ] `GET /api/testcases/template` - 下载模板

**前端组件**:
- [ ] `TestCasePanel.tsx` - 用例管理面板
- [ ] `useTestCases.ts` - 用例管理Hook
- [ ] 文件拖拽上传组件
- [ ] 用例列表和编辑功能

#### 2.3 两阶段页面实现
- [ ] `PreparePage.tsx` - 准备工作台页面
- [ ] 配置面板和用例面板的布局整合
- [ ] 准备就绪状态检查
- [ ] 页面间导航和状态传递

### 第三阶段：执行监控功能 (2-3天)

#### 3.1 测试执行模块
**后端API**:
- [ ] `POST /api/test/start` - 开始测试
- [ ] `POST /api/test/pause` - 暂停测试
- [ ] `POST /api/test/stop` - 停止测试
- [ ] `GET /api/test/status` - 获取状态
- [ ] `GET /api/test/logs` - 获取日志流 (SSE)

**前端组件**:
- [ ] `ExecutionPanel.tsx` - 执行控制面板
- [ ] `useExecution.ts` - 执行管理Hook
- [ ] 实时进度条和状态显示
- [ ] SSE连接和实时日志显示

#### 3.2 结果管理模块
**后端API**:
- [ ] `GET /api/results` - 获取结果列表
- [ ] `GET /api/results/{id}` - 获取结果详情
- [ ] `POST /api/results/export` - 导出结果

**前端组件**:
- [ ] `ResultPanel.tsx` - 结果展示面板
- [ ] 统计信息展示
- [ ] 结果列表和详情查看
- [ ] 导出功能实现

#### 3.3 执行监控页面
- [ ] `ExecutePage.tsx` - 执行监控台页面
- [ ] 执行面板和结果面板的布局整合
- [ ] 实时数据更新和状态同步

### 第四阶段：完善和优化 (1-2天)

#### 4.1 用户体验优化
- [ ] 执行状态锁定：测试运行时禁用配置和用例编辑
- [ ] 长日志处理：前端只渲染最近500条，提供完整日志导出
- [ ] 资源占用提示：友好的执行状态提示
- [ ] 错误处理和用户反馈
- [ ] 加载状态和进度指示
- [ ] 响应式布局适配

#### 4.2 数据持久化和安全
- [ ] 文件存储结构设计和初始化
- [ ] 首次启动自动导入现有config.ini
- [ ] API密钥加密存储 (cryptography + 机器绑定)
- [ ] 配置导入导出功能
- [ ] 测试历史记录管理

#### 4.3 测试和文档
- [ ] 功能测试和边界测试
- [ ] 性能测试 (大文件上传、长时间执行)
- [ ] 用户手册和API文档
- [ ] 部署指南

## 🛠️ 技术栈确认

### 前端
- **框架**: React 18 + TypeScript
- **UI库**: Ant Design 5.x
- **状态管理**: React Hooks + Context (简单场景)
- **构建工具**: Vite
- **HTTP客户端**: Axios
- **文件处理**: SheetJS (xlsx)

### 后端
- **框架**: FastAPI
- **数据验证**: Pydantic
- **文件处理**: 复用现有 `excel_handler.py`
- **实时通信**: Server-Sent Events (SSE)
- **代码复用**: 导入现有 `src/` 模块

## 📦 交付清单

### 代码交付
- [ ] 完整的前端应用 (`web/frontend/`)
- [ ] 完整的后端API (`web/backend/`)
- [ ] 启动脚本 (`web/start.py`)
- [ ] 依赖文件 (`web/requirements-web.txt`)

### 文档交付
- [ ] Web使用说明 (`web/README-web.md`)
- [ ] API接口文档 (FastAPI自动生成)
- [ ] 开发者文档 (代码结构说明)

### 测试交付
- [ ] 功能测试用例
- [ ] 兼容性测试报告
- [ ] 性能测试报告

## 🎯 验收标准

### 功能验收
- [ ] 配置管理：创建、编辑、删除、切换配置
- [ ] 用例管理：上传文件、编辑用例、下载模板
- [ ] 测试执行：开始、暂停、停止，实时进度显示
- [ ] 结果查看：统计信息、结果列表、导出功能
- [ ] 原有命令行功能完全不受影响

### 性能验收
- [ ] 页面加载时间 < 3秒
- [ ] 支持1000+测试用例流畅操作
- [ ] 文件上传进度实时显示
- [ ] 实时日志更新无卡顿

### 兼容性验收
- [ ] Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- [ ] 1280x720 以上分辨率正常显示
- [ ] Windows 10/11 本地部署成功

## 📈 风险评估

### 技术风险
- **中等**: 现有Python模块的导入和封装
- **低**: 前端组件开发和API集成
- **低**: 实时数据推送 (SSE相对简单)

### 进度风险
- **低**: 项目规模适中，技术栈成熟
- **中等**: 需要保证不影响现有功能

### 缓解措施
- 优先实现核心功能，次要功能可后续迭代
- 充分测试现有功能的兼容性
- 保持代码结构清晰，便于维护和扩展

---

**计划制定日期**: 2024-01-15  
**预计开发周期**: 7-10天  
**计划完成日期**: 2024-01-25