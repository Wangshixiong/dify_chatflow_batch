import React, { useState } from 'react';
import { Row, Col, Card, Steps, Button, Alert, Space, Divider, message } from 'antd';
import {
  SettingOutlined,
  FileTextOutlined,
  RocketOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import ConfigPanel from '../components/ConfigPanel';
import TestCasePanel from '../components/TestCasePanel';

const { Step } = Steps;

interface PreparePageProps {
  onStartTest?: () => void;
}

const PreparePage: React.FC<PreparePageProps> = ({ onStartTest }) => {
  const [activeConfig, setActiveConfig] = useState<string | null>(null);
  const [testCasesCount, setTestCasesCount] = useState(0);

  // 检查是否准备就绪
  const isReady = activeConfig && testCasesCount > 0;

  const handleStartTest = () => {
    if (!activeConfig) {
      message.warning('请先创建并激活一个配置！');
      return;
    }
    if (testCasesCount === 0) {
      message.warning('请先上传或添加测试用例！');
      return;
    }
    if (isReady) {
      message.success('✨ 准备就绪，正在进入执行阶段...');
      // 直接跳转到执行页面，由ExecutePage负责自动启动
      onStartTest?.();
    }
  };

  return (
    <div style={{ padding: '24px', backgroundColor: '#f5f5f5', minHeight: '100vh' }}>
      {/* 页面标题和步骤指示 */}
      <Card style={{ marginBottom: '24px' }}>
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <h1 style={{ fontSize: '24px', marginBottom: '8px' }}>
            📋 准备工作台
          </h1>
          <p style={{ color: '#666', fontSize: '16px' }}>
            配置测试参数和准备测试用例，开始批量测试之旅
          </p>
        </div>

        <Steps current={isReady ? 2 : (activeConfig ? 1 : 0)} style={{ maxWidth: '600px', margin: '0 auto' }}>
          <Step
            title="配置管理"
            description="设置API参数"
            icon={<SettingOutlined />}
            status={activeConfig ? 'finish' : 'process'}
          />
          <Step
            title="测试用例"
            description="准备测试数据"
            icon={<FileTextOutlined />}
            status={testCasesCount > 0 ? 'finish' : (activeConfig ? 'process' : 'wait')}
          />
          <Step
            title="开始测试"
            description="执行批量测试"
            icon={<RocketOutlined />}
            status={isReady ? 'process' : 'wait'}
          />
        </Steps>
      </Card>

      {/* 主要内容区域 */}
      <Row gutter={[24, 24]}>
        {/* 左侧：配置管理 */}
        <Col xs={24} lg={12}>
          <ConfigPanel onConfigChange={setActiveConfig} />
        </Col>

        {/* 右侧：测试用例管理 */}
        <Col xs={24} lg={12}>
          <TestCasePanel onCasesChange={setTestCasesCount} />
        </Col>
      </Row>

      {/* 准备就绪检查和开始按钮 */}
      <Card style={{ marginTop: '24px' }}>
        <div style={{ textAlign: 'center' }}>
          <h3 style={{ marginBottom: '16px' }}>
            <CheckCircleOutlined style={{ color: '#52c41a', marginRight: '8px' }} />
            准备就绪检查
          </h3>

          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            {/* 配置检查 */}
            <Alert
              message={
                <Space>
                  <span>配置状态:</span>
                  {activeConfig ? (
                    <span style={{ color: '#52c41a' }}>
                      ✅ 已选择配置 "{activeConfig}"
                    </span>
                  ) : (
                    <span style={{ color: '#ff4d4f' }}>
                      ❌ 请先创建并激活一个配置
                    </span>
                  )}
                </Space>
              }
              type={activeConfig ? 'success' : 'warning'}
              showIcon
            />

            {/* 测试用例检查 */}
            <Alert
              message={
                <Space>
                  <span>测试用例:</span>
                  {testCasesCount > 0 ? (
                    <span style={{ color: '#52c41a' }}>
                      ✅ 已加载 {testCasesCount} 条测试用例
                    </span>
                  ) : (
                    <span style={{ color: '#ff4d4f' }}>
                      ❌ 请先上传或添加测试用例
                    </span>
                  )}
                </Space>
              }
              type={testCasesCount > 0 ? 'success' : 'warning'}
              showIcon
            />

            {/* API连接检查提示 */}
            {activeConfig && (
              <Alert
                message="💡 建议在开始测试前，先测试API连接确保配置正确"
                type="info"
                showIcon
              />
            )}

            <Divider />

            {/* 开始测试按钮 */}
            <Button
              type="primary"
              size="large"
              icon={<RocketOutlined />}
              onClick={handleStartTest}
              disabled={!isReady}
              style={{
                height: '48px',
                fontSize: '16px',
                minWidth: '200px',
              }}
            >
              {isReady ? '🚀 开始测试' : '请完成准备工作'}
            </Button>

            {isReady && (
              <p style={{ color: '#666', marginTop: '8px' }}>
                点击后将进入执行监控台，开始批量测试
              </p>
            )}
          </Space>
        </div>
      </Card>

      {/* 使用提示 */}
      <Card title="💡 使用提示" style={{ marginTop: '24px' }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} md={8}>
            <div>
              <h4>📝 配置管理</h4>
              <ul style={{ paddingLeft: '20px', color: '#666' }}>
                <li>支持多套配置方案</li>
                <li>API密钥自动加密存储</li>
                <li>可测试连接验证配置</li>
                <li>首次使用已自动导入现有配置</li>
              </ul>
            </div>
          </Col>
          <Col xs={24} md={8}>
            <div>
              <h4>📋 测试用例</h4>
              <ul style={{ paddingLeft: '20px', color: '#666' }}>
                <li>支持Excel/CSV文件上传</li>
                <li>可下载标准模板</li>
                <li>支持手动添加和编辑</li>
                <li>自动验证数据格式</li>
              </ul>
            </div>
          </Col>
          <Col xs={24} md={8}>
            <div>
              <h4>🚀 测试执行</h4>
              <ul style={{ paddingLeft: '20px', color: '#666' }}>
                <li>支持暂停和恢复</li>
                <li>实时显示执行进度</li>
                <li>自动保存测试结果</li>
                <li>支持多种格式导出</li>
              </ul>
            </div>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default PreparePage;