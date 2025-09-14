import { useState } from 'react';
import { ConfigProvider, Layout, message } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import PreparePage from './pages/PreparePage';
import ExecutePage from './pages/ExecutePage';
import './App.css';

const { Header, Content } = Layout;

function App() {
  const [currentStage, setCurrentStage] = useState<'prepare' | 'execute'>('prepare');
  const [shouldAutoStart, setShouldAutoStart] = useState(false);

  const handleStartTest = () => {
    message.success('🚀 正在进入执行阶段...', 1.5);
    setShouldAutoStart(true); // 设置自动启动标志
    setTimeout(() => {
      setCurrentStage('execute');
    }, 500);
  };

  const handleBackToPrepare = () => {
    message.info('📋 返回准备阶段...', 1);
    setShouldAutoStart(false); // 重置自动启动标志
    setTimeout(() => {
      setCurrentStage('prepare');
    }, 300);
  };

  return (
    <ConfigProvider locale={zhCN}>
      <Layout style={{ minHeight: '100vh' }}>
        <Header style={{ 
          background: 'linear-gradient(135deg, #1890ff 0%, #722ed1 100%)',
          display: 'flex',
          alignItems: 'center',
          padding: '0 24px'
        }}>
          <h1 style={{ 
            color: 'white', 
            margin: 0, 
            fontSize: '20px',
            fontWeight: 600
          }}>
            Dify ChatFlow Batch Tool
          </h1>
          <div style={{ 
            marginLeft: 'auto', 
            color: 'rgba(255,255,255,0.8)',
            fontSize: '14px'
          }}>
            {currentStage === 'prepare' ? '📋 准备阶段' : '🚀 执行阶段'}
          </div>
        </Header>
        
        <Content style={{ padding: 0 }}>
          {currentStage === 'prepare' ? (
            <PreparePage onStartTest={handleStartTest} />
          ) : (
            <ExecutePage 
              onBackToPrepare={handleBackToPrepare} 
              shouldAutoStart={shouldAutoStart}
              onAutoStartComplete={() => setShouldAutoStart(false)}
            />
          )}
        </Content>
      </Layout>
    </ConfigProvider>
  );
}

export default App;