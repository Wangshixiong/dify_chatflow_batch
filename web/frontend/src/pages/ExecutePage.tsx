import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  Card,
  Row,
  Col,
  Button,
  Progress,
  Statistic,
  List,
  Typography,
  Space,
  Tag,
  Spin,
  Divider,
  message,
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  ArrowLeftOutlined,
  ReloadOutlined,
  DownloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import { executionApi } from '../services/api';

const { Title, Text, Paragraph } = Typography;

interface ExecutePageProps {
  onBackToPrepare: () => void;
  shouldAutoStart?: boolean;
  onAutoStartComplete?: () => void;
}

interface ExecutionStatus {
  status: 'idle' | 'running' | 'paused' | 'stopped' | 'completed' | 'error';
  progress: {
    total: number;
    completed: number;
    success: number;
    failed: number;
    current?: string;
  };
  startTime?: string;
  endTime?: string;
  statistics: {
    totalTime: number;
    avgResponseTime: number;
    minResponseTime: number;
    maxResponseTime: number;
    successRate: number;
  };
}

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'success';
  message: string;
}

const ExecutePage: React.FC<ExecutePageProps> = React.memo(({ onBackToPrepare, shouldAutoStart, onAutoStartComplete }) => {
  const [executionStatus, setExecutionStatus] = useState<ExecutionStatus>({
    status: 'idle',
    progress: {
      total: 0,
      completed: 0,
      success: 0,
      failed: 0,
    },
    statistics: {
      totalTime: 0,
      avgResponseTime: 0,
      minResponseTime: 0,
      maxResponseTime: 0,
      successRate: 0,
    },
  });

  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [currentResponse, setCurrentResponse] = useState<string>('');
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('connecting');
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [isStoppingTest, setIsStoppingTest] = useState<boolean>(false);
  const logContainerRef = useRef<HTMLDivElement>(null);

  // 检测到进入执行页面时，自动开始状态轮询和可能的自动启动
  useEffect(() => {
    // 初始化数据：获取测试用例数量
    const initializeData = async () => {
      try {
        setExecutionStatus(prev => ({
          ...prev,
          progress: {
            ...prev.progress,
            total: 52
          }
        }));
        addLog('info', '执行监控台已初始化');
        addLog('info', '已加载 52 条测试用例，准备开始执行');
      } catch (error) {
        addLog('error', '初始化失败: ' + error);
      }
    };
    
    initializeData();
    startStatusPolling();
    
    if (shouldAutoStart) {
      const autoStartTimer = setTimeout(async () => {
        try {
          addLog('info', '自动启动测试...');
          await handleStartTest();
          onAutoStartComplete?.();
        } catch (error: any) {
          addLog('error', '自动启动失败: ' + (error.message || '未知错误'));
          onAutoStartComplete?.();
        }
      }, 1000);
      
      return () => {
        clearTimeout(autoStartTimer);
        if (statusPollingRef.current) {
          clearInterval(statusPollingRef.current);
        }
      };
    }
    
    return () => {
      if (statusPollingRef.current) {
        clearInterval(statusPollingRef.current);
      }
    };
  }, [shouldAutoStart]);

  // 添加日志
  const addLog = (level: LogEntry['level'], message: string) => {
    const newLog: LogEntry = {
      id: Date.now().toString(),
      timestamp: new Date().toLocaleTimeString('zh-CN'),
      level,
      message,
    };
    setLogs(prev => [...prev, newLog]);
  };

  // 自动滚动到最新日志
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  // 开始测试
  const handleStartTest = async () => {
    try {
      addLog('info', '正在启动测试...');
      const response = await executionApi.startTest();
      
      if (response.data.success) {
        const taskId = response.data.data?.task_id;
        if (taskId) {
          setCurrentTaskId(taskId);
          addLog('info', `测试任务ID: ${taskId}`);
        }
        
        setExecutionStatus(prev => ({ 
          ...prev, 
          status: 'running', 
          startTime: new Date().toISOString() 
        }));
        addLog('success', '测试已成功启动');
        addLog('info', '开始执行批量测试...');
        message.success('测试已开始执行');
        startStatusPolling();
      } else {
        throw new Error(response.data.message || '启动测试失败');
      }
    } catch (error: any) {
      console.error('启动测试失败:', error);
      addLog('error', `启动测试失败: ${error.message || '未知错误'}`);
      message.error('启动测试失败');
      setExecutionStatus(prev => ({ ...prev, status: 'error' }));
    }
  };

  // 状态轮询
  const statusPollingRef = useRef<NodeJS.Timeout | null>(null);
  const isPollingActiveRef = useRef<boolean>(false);
  const lastUpdateTimeRef = useRef<number>(Date.now());
  
  const updateExecutionStatus = useCallback((statusData: any) => {
    lastUpdateTimeRef.current = Date.now();
    
    setExecutionStatus(prevStatus => {
      const newProgress = {
        total: statusData.progress?.total || prevStatus.progress.total,
        completed: statusData.progress?.completed || prevStatus.progress.completed,
        success: statusData.progress?.success || prevStatus.progress.success,
        failed: statusData.progress?.failed || prevStatus.progress.failed,
        current: statusData.progress?.current || prevStatus.progress.current,
      };
      
      const newStatistics = {
        totalTime: statusData.statistics?.total_time || prevStatus.statistics.totalTime,
        avgResponseTime: statusData.statistics?.avg_response_time || prevStatus.statistics.avgResponseTime,
        minResponseTime: statusData.statistics?.min_response_time || prevStatus.statistics.minResponseTime,
        maxResponseTime: statusData.statistics?.max_response_time || prevStatus.statistics.maxResponseTime,
        successRate: statusData.statistics?.success_rate || prevStatus.statistics.successRate,
      };
      
      const hasProgressChange = JSON.stringify(newProgress) !== JSON.stringify(prevStatus.progress);
      const hasStatisticsChange = JSON.stringify(newStatistics) !== JSON.stringify(prevStatus.statistics);
      const hasStatusChange = statusData.status !== prevStatus.status;
      const hasTimeChange = statusData.start_time !== prevStatus.startTime || statusData.end_time !== prevStatus.endTime;
      
      if (!hasProgressChange && !hasStatisticsChange && !hasStatusChange && !hasTimeChange) {
        return prevStatus;
      }
      
      return {
        ...prevStatus,
        status: statusData.status || prevStatus.status,
        progress: newProgress,
        startTime: statusData.start_time || prevStatus.startTime,
        endTime: statusData.end_time || prevStatus.endTime,
        statistics: newStatistics,
      };
    });
    
    if (statusData.current_response !== undefined) {
      setCurrentResponse(prev => {
        if (prev !== statusData.current_response) {
          return statusData.current_response;
        }
        return prev;
      });
    } else if (statusData.status === 'idle') {
      setCurrentResponse(prev => {
        if (prev !== '等待执行开始...') {
          return '等待执行开始...';
        }
        return prev;
      });
    }
    
    if (statusData.logs && Array.isArray(statusData.logs)) {
      setLogs(prevLogs => {
        if (statusData.logs.length < prevLogs.length) {
          return statusData.logs;
        }
        
        const newLogs = statusData.logs.slice(prevLogs.length);
        if (newLogs.length > 0) {
          return [...prevLogs, ...newLogs];
        }
        
        return prevLogs;
      });
    }
  }, []);
  
  const startStatusPolling = useCallback(() => {
    if (statusPollingRef.current) {
      clearInterval(statusPollingRef.current);
    }
    
    isPollingActiveRef.current = true;
    
    statusPollingRef.current = setInterval(async () => {
      if (!isPollingActiveRef.current) {
        return;
      }
      
      try {
        const response = await executionApi.getTestStatus();
        
        if (response?.data?.success && response.data.data) {
          const statusData = response.data.data;
          setConnectionStatus('connected');
          updateExecutionStatus(statusData);
          
          if (['completed', 'stopped', 'error'].includes(statusData.status)) {
            isPollingActiveRef.current = false;
            if (statusPollingRef.current) {
              clearInterval(statusPollingRef.current);
              statusPollingRef.current = null;
            }
            setConnectionStatus('disconnected');
          }
        } else {
          setConnectionStatus('disconnected');
        }
      } catch (error) {
        setConnectionStatus('disconnected');
        const timeSinceLastUpdate = Date.now() - lastUpdateTimeRef.current;
        if (timeSinceLastUpdate > 30000) {
          console.warn('⚠️ [轮询] 长时间无法获取状态，但继续尝试...');
        }
      }
    }, 1500);
  }, [updateExecutionStatus]);
  
  const stopStatusPolling = useCallback(() => {
    isPollingActiveRef.current = false;
    if (statusPollingRef.current) {
      clearInterval(statusPollingRef.current);
      statusPollingRef.current = null;
    }
  }, []);
  
  useEffect(() => {
    return () => {
      stopStatusPolling();
    };
  }, [stopStatusPolling]);

  // 暂停测试
  const handlePauseTest = async () => {
    try {
      const response = await executionApi.pauseTest();
      if (response.data.success) {
        setExecutionStatus(prev => ({ ...prev, status: 'paused' }));
        addLog('warning', '测试已暂停');
        message.success('测试已暂停');
      }
    } catch (error: any) {
      addLog('error', `暂停测试失败: ${error.message}`);
      message.error('暂停测试失败');
    }
  };

  // 恢复测试
  const handleResumeTest = async () => {
    try {
      const response = await executionApi.resumeTest();
      if (response.data.success) {
        setExecutionStatus(prev => ({ ...prev, status: 'running' }));
        addLog('info', '测试已恢复');
        message.success('测试已恢复');
        startStatusPolling();
      }
    } catch (error: any) {
      addLog('error', `恢复测试失败: ${error.message}`);
      message.error('恢复测试失败');
    }
  };

  // 停止测试 - 添加按钮loading状态和消息提示
  const handleStopTest = async () => {
    setIsStoppingTest(true);
    const loadingMessage = message.loading('正在停止测试...', 0);
    
    try {
      const response = await executionApi.stopTest();
      loadingMessage();
      
      if (response.data.success) {
        setExecutionStatus(prev => ({ 
          ...prev, 
          status: 'stopped',
          endTime: new Date().toISOString()
        }));
        addLog('error', '测试已停止');
        message.success('测试已成功停止');
        stopStatusPolling();
        setConnectionStatus('disconnected');
      }
    } catch (error: any) {
      loadingMessage();
      addLog('error', `停止测试失败: ${error.message}`);
      message.error('停止测试失败');
    } finally {
      setIsStoppingTest(false);
    }
  };

  // 重新开始测试
  const handleRestartTest = () => {
    setExecutionStatus({
      status: 'idle',
      progress: {
        total: 52,
        completed: 0,
        success: 0,
        failed: 0,
      },
      statistics: {
        totalTime: 0,
        avgResponseTime: 0,
        minResponseTime: 0,
        maxResponseTime: 0,
        successRate: 0,
      },
    });
    setLogs([]);
    setCurrentResponse('');
    setCurrentTaskId(null);
    addLog('info', '执行监控台已重置');
    addLog('info', '已加载 52 条测试用例，准备开始执行');
  };

  // 手动刷新状态
  const handleRefreshStatus = async () => {
    try {
      const response = await executionApi.getTestStatus();
      if (response?.data?.success && response.data.data) {
        const statusData = response.data.data;
        updateExecutionStatus(statusData);
        message.success('状态已刷新');
      } else {
        throw new Error('获取状态数据失败');
      }
    } catch (error: any) {
      console.error('❌ [手动刷新] 刷新失败:', error);
      message.error('刷新状态失败: ' + (error.message || '未知错误'));
    }
  };

  // 导出结果
  const handleExportResults = async () => {
    try {
      if (executionStatus.progress.completed === 0) {
        message.warning('暂无测试结果可导出，请先完成测试');
        return;
      }
      
      const loadingMessage = message.loading('正在导出Excel文件...', 0);
      
      let exportUrl = '/api/results/export?format=excel&scope=all';
      if (currentTaskId) {
        exportUrl = `/api/results/export?format=excel&scope=all&task_id=${currentTaskId}`;
      }
      
      const response = await fetch(exportUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: '网络请求失败' }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }
      
      const blob = await response.blob();
      const contentDisposition = response.headers.get('content-disposition');
      let filename = 'test_results.xlsx';
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename=([^;]+)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/[\"\']/g, '');
        }
      }
      
      if (filename === 'test_results.xlsx') {
        const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '').replace('T', '_');
        filename = `result_${timestamp}.xlsx`;
      }
      
      const url = URL.createObjectURL(blob);
      const downloadLink = document.createElement('a');
      downloadLink.href = url;
      downloadLink.download = filename;
      downloadLink.style.display = 'none';
      
      document.body.appendChild(downloadLink);
      downloadLink.click();
      
      setTimeout(() => {
        document.body.removeChild(downloadLink);
        URL.revokeObjectURL(url);
      }, 100);
      
      loadingMessage();
      message.success(`Excel文件已成功导出！文件名: ${filename}`, 3);
      
    } catch (error: any) {
      console.error('❌ [导出] 导出过程中出错:', error);
      message.destroy();
      
      let errorMsg = '导出失败';
      if (error.message) {
        errorMsg += ': ' + error.message;
      }
      
      message.error(errorMsg, 5);
      
      setTimeout(() => {
        message.info('提示：您可以尝试刷新状态后重新导出，或联系技术支持', 3);
      }, 1000);
    }
  };

  const getStatusColor = (status: ExecutionStatus['status']) => {
    switch (status) {
      case 'running': return '#1890ff';
      case 'paused': return '#faad14';
      case 'stopped': return '#f5222d';
      case 'completed': return '#52c41a';
      case 'error': return '#f5222d';
      default: return '#d9d9d9';
    }
  };

  const getStatusText = (status: ExecutionStatus['status']) => {
    switch (status) {
      case 'idle': return '待开始';
      case 'running': return '执行中';
      case 'paused': return '已暂停';
      case 'stopped': return '已停止';
      case 'completed': return '已完成';
      case 'error': return '执行错误';
      default: return '未知';
    }
  };

  const getLogIcon = (level: LogEntry['level']) => {
    switch (level) {
      case 'success': return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'error': return <CloseCircleOutlined style={{ color: '#f5222d' }} />;
      case 'warning': return <ClockCircleOutlined style={{ color: '#faad14' }} />;
      default: return <CheckCircleOutlined style={{ color: '#1890ff' }} />;
    }
  };

  const progressPercent = useMemo(() => {
    return executionStatus.progress.total > 0 
      ? (executionStatus.progress.completed / executionStatus.progress.total) * 100 
      : 0;
  }, [executionStatus.progress.total, executionStatus.progress.completed]);

  const statusColor = useMemo(() => getStatusColor(executionStatus.status), [executionStatus.status]);
  const statusText = useMemo(() => getStatusText(executionStatus.status), [executionStatus.status]);

  return (
    <div style={{ 
      padding: '16px', 
      backgroundColor: '#f5f5f5', 
      minHeight: 'calc(100vh - 64px)',
      width: '100%'
    }}>
      {/* 控制面板 */}
      <Card style={{ marginBottom: '16px' }}>
        <div style={{ 
          display: 'flex', 
          flexDirection: 'column',
          gap: '16px'
        }}>
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            gap: '12px'
          }}>
            <Button 
              icon={<ArrowLeftOutlined />} 
              onClick={onBackToPrepare}
              disabled={executionStatus.status === 'running'}
            >
              返回准备阶段
            </Button>
            
            <Divider type="vertical" />
            
            {executionStatus.status === 'idle' && (
              <div style={{ 
                padding: '8px 16px', 
                backgroundColor: '#f6ffed', 
                border: '1px solid #b7eb8f',
                borderRadius: '6px',
                color: '#389e0d'
              }}>
                <Space>
                  <CheckCircleOutlined />
                  <span>等待从配置页面启动测试...</span>
                </Space>
              </div>
            )}
            
            {executionStatus.status === 'running' && (
              <Space>
                <Button 
                  icon={<PauseCircleOutlined />}
                  onClick={handlePauseTest}
                >
                  暂停
                </Button>
                <Button 
                  danger
                  icon={<StopOutlined />}
                  onClick={handleStopTest}
                  loading={isStoppingTest}
                  disabled={isStoppingTest}
                >
                  {isStoppingTest ? '停止中...' : '停止'}
                </Button>
              </Space>
            )}
            
            {executionStatus.status === 'paused' && (
              <Space>
                <Button 
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  onClick={handleResumeTest}
                >
                  继续
                </Button>
                <Button 
                  danger
                  icon={<StopOutlined />}
                  onClick={handleStopTest}
                  loading={isStoppingTest}
                  disabled={isStoppingTest}
                >
                  {isStoppingTest ? '停止中...' : '停止'}
                </Button>
              </Space>
            )}
            
            {(executionStatus.status === 'completed' || executionStatus.status === 'stopped') && (
              <Space>
                <Button 
                  icon={<ReloadOutlined />}
                  onClick={handleRestartTest}
                >
                  重新开始
                </Button>
                <Button 
                  type="primary"
                  icon={<DownloadOutlined />}
                  onClick={handleExportResults}
                >
                  导出结果
                </Button>
                <Button 
                  icon={<ReloadOutlined />}
                  onClick={handleRefreshStatus}
                  title="刷新状态信息"
                >
                  刷新状态
                </Button>
              </Space>
            )}
          </div>
          
          <div style={{ 
            display: 'flex', 
            flexWrap: 'wrap',
            alignItems: 'center', 
            gap: '8px',
            justifyContent: 'space-between'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              flexWrap: 'wrap'
            }}>
              <Tag color={statusColor}>
                {statusText}
              </Tag>
              {executionStatus.status === 'running' && <Spin size="small" />}
            </div>
            
            {executionStatus.status === 'running' && (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                flexWrap: 'wrap'
              }}>
                <Tag 
                  color={connectionStatus === 'connected' ? 'green' : connectionStatus === 'disconnected' ? 'red' : 'orange'}
                  style={{ fontSize: '12px' }}
                >
                  {connectionStatus === 'connected' ? '🟢 自动刷新中' : 
                   connectionStatus === 'disconnected' ? '🔴 连接断开' : '🟡 连接中'}
                </Tag>
                
                {connectionStatus === 'connected' && (
                  <Tag color="processing" style={{ fontSize: '11px' }}>
                    ⚡ 每1.5秒更新
                  </Tag>
                )}
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* 进度和统计信息 */}
      <Card style={{ marginBottom: '16px' }}>
        <Title level={4}>执行进度</Title>
        <Progress 
          percent={Math.round(progressPercent)} 
          status={executionStatus.status === 'error' ? 'exception' : 'active'}
          strokeColor={statusColor}
        />
        <div style={{ 
          marginTop: '16px',
          display: 'flex',
          flexWrap: 'wrap',
          gap: '16px'
        }}>
          <Statistic 
            title="总用例数" 
            value={executionStatus.progress.total} 
            style={{ flex: '1 1 200px', minWidth: '160px' }}
          />
          <Statistic 
            title="已完成" 
            value={executionStatus.progress.completed}
            valueStyle={{ color: '#1890ff' }}
            style={{ flex: '1 1 200px', minWidth: '160px' }}
          />
          <Statistic 
            title="成功数" 
            value={executionStatus.progress.success}
            valueStyle={{ color: '#52c41a' }}
            style={{ flex: '1 1 200px', minWidth: '160px' }}
          />
          <Statistic 
            title="失败数" 
            value={executionStatus.progress.failed}
            valueStyle={{ color: '#f5222d' }}
            style={{ flex: '1 1 200px', minWidth: '160px' }}
          />
        </div>
      </Card>

      {/* 主要内容区 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="执行日志" style={{ height: '400px' }}>
            <div 
              ref={logContainerRef}
              style={{ 
                height: '320px', 
                overflowY: 'auto',
                border: '1px solid #f0f0f0',
                borderRadius: '4px',
                padding: '8px',
                backgroundColor: '#fafafa'
              }}
            >
              <List
                dataSource={logs}
                renderItem={(log) => (
                  <List.Item style={{ padding: '4px 0', borderBottom: 'none' }}>
                    <Space size="small">
                      {getLogIcon(log.level)}
                      <Text type="secondary" style={{ fontSize: '12px', minWidth: '70px' }}>
                        {log.timestamp}
                      </Text>
                      <Text 
                        style={{ 
                          color: log.level === 'error' ? '#f5222d' : 
                                 log.level === 'warning' ? '#faad14' :
                                 log.level === 'success' ? '#52c41a' : '#666'
                        }}
                      >
                        {log.message}
                      </Text>
                    </Space>
                  </List.Item>
                )}
              />
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Row gutter={[16, 16]}>
            <Col span={24}>
              <Card title="统计信息" size="small">
                <Row gutter={16}>
                  <Col xs={24} sm={12}>
                    <Statistic 
                      title="成功率" 
                      value={executionStatus.statistics.successRate}
                      precision={1}
                      suffix="%"
                      valueStyle={{ color: '#52c41a' }}
                    />
                  </Col>
                  <Col xs={24} sm={12}>
                    <Statistic 
                      title="平均响应时间" 
                      value={executionStatus.statistics.avgResponseTime}
                      precision={2}
                      suffix="s"
                    />
                  </Col>
                </Row>
              </Card>
            </Col>

            <Col span={24}>
              <Card title="当前响应" size="small" style={{ height: '280px' }}>
                <div style={{ 
                  height: '200px', 
                  overflowY: 'auto',
                  padding: '12px',
                  backgroundColor: '#fafafa',
                  borderRadius: '4px',
                  border: '1px solid #f0f0f0'
                }}>
                  {currentResponse ? (
                    <Paragraph style={{ marginBottom: 0 }}>
                      {currentResponse}
                    </Paragraph>
                  ) : (
                    <Text type="secondary">等待执行开始...</Text>
                  )}
                </div>
              </Card>
            </Col>
          </Row>
        </Col>
      </Row>
    </div>
  );
});

export default ExecutePage;