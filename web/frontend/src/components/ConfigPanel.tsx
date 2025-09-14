import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Form,
  Input,
  Select,
  InputNumber,
  Switch,
  Modal,
  message,
  Popconfirm,
  Space,
  Tag,
  Tooltip,
  Spin,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  ApiOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { configApi } from '../services/api';
import type { Config, ConfigCreate, ConfigUpdate } from '../types';

const { Option } = Select;

interface ConfigPanelProps {
  onConfigChange?: (activeConfig: string | null) => void;
}

const ConfigPanel: React.FC<ConfigPanelProps> = ({ onConfigChange }) => {
  const [configs, setConfigs] = useState<Config[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingConfig, setEditingConfig] = useState<Config | null>(null);
  const [testingConnection, setTestingConnection] = useState<string | null>(null);
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([]);
  const [form] = Form.useForm();

  // 加载配置列表
  const loadConfigs = async () => {
    setLoading(true);
    try {
      const response = await configApi.getConfigs();
      if (response.data.success) {
        setConfigs(response.data.data || []);
        // 通知父组件当前活跃配置
        const activeConfig = response.data.data?.find((c: Config) => c.is_active);
        onConfigChange?.(activeConfig?.name || null);
      } else {
        message.error(response.data.message);
      }
    } catch (error) {
      message.error('加载配置失败');
      console.error('Load configs error:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConfigs();
  }, []);

  // 创建配置
  const handleCreate = async (values: ConfigCreate) => {
    try {
      const response = await configApi.createConfig(values);
      if (response.data.success) {
        message.success('配置创建成功');
        setShowCreateModal(false);
        form.resetFields();
        loadConfigs();
      } else {
        message.error(response.data.message);
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '创建配置失败');
    }
  };

  // 更新配置
  const handleUpdate = async (values: ConfigUpdate) => {
    if (!editingConfig) return;
    
    try {
      const response = await configApi.updateConfig(editingConfig.name, values);
      if (response.data.success) {
        message.success('配置更新成功');
        setShowEditModal(false);
        setEditingConfig(null);
        form.resetFields();
        loadConfigs();
      } else {
        message.error(response.data.message);
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '更新配置失败');
    }
  };

  // 删除配置
  const handleDelete = async (name: string) => {
    try {
      const response = await configApi.deleteConfig(name);
      if (response.data.success) {
        message.success('配置删除成功');
        loadConfigs();
      } else {
        message.error(response.data.message);
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除配置失败');
    }
  };

  // 批量删除配置
  const handleBatchDelete = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要删除的配置');
      return;
    }

    // 检查是否包含默认配置
    if (selectedRowKeys.includes('default')) {
      message.error('不能删除默认配置');
      return;
    }

    try {
      // 并发删除所有选中的配置
      const deletePromises = selectedRowKeys.map(name => configApi.deleteConfig(name));
      const results = await Promise.allSettled(deletePromises);
      
      const successCount = results.filter(result => 
        result.status === 'fulfilled' && result.value.data.success
      ).length;
      
      if (successCount === selectedRowKeys.length) {
        message.success(`成功删除 ${successCount} 个配置`);
      } else {
        message.warning(`删除了 ${successCount}/${selectedRowKeys.length} 个配置`);
      }
      
      setSelectedRowKeys([]);
      loadConfigs();
    } catch (error: any) {
      message.error('批量删除失败');
      console.error('Batch delete error:', error);
    }
  };

  // 激活配置
  const handleActivate = async (name: string) => {
    try {
      const response = await configApi.activateConfig(name);
      if (response.data.success) {
        message.success('配置已激活');
        loadConfigs();
      } else {
        message.error(response.data.message);
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '激活配置失败');
    }
  };

  // 测试连接
  const handleTestConnection = async (config: Config) => {
    setTestingConnection(config.name);
    try {
      const response = await configApi.testConfigConnection(config.name);
      if (response.data.success) {
        message.success(`连接测试成功 (${response.data.response_time}s)`);
      } else {
        message.error(response.data.message);
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '连接测试失败');
    } finally {
      setTestingConnection(null);
    }
  };

  // 编辑配置
  const handleEdit = (config: Config) => {
    setEditingConfig(config);
    form.setFieldsValue({
      name: config.name,
      api_url: config.api_url,
      user_id: config.user_id,
      timeout: config.timeout,
      response_mode: config.response_mode,
      log_level: config.log_level,
      output_dir: config.output_dir,
      include_timestamp: config.include_timestamp,
    });
    setShowEditModal(true);
  };

  // 行选择配置
  const rowSelection = {
    selectedRowKeys,
    onChange: (newSelectedRowKeys: React.Key[]) => {
      setSelectedRowKeys(newSelectedRowKeys as string[]);
    },
    getCheckboxProps: (record: Config) => ({
      disabled: record.name === 'default', // 默认配置不能选择
    }),
  };

  // 表格列定义
  const columns: ColumnsType<Config> = [
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'status',
      width: 80,
      align: 'center',
      render: (isActive: boolean) => (
        isActive ? (
          <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 16 }} />
        ) : (
          <SettingOutlined style={{ color: '#d9d9d9', fontSize: 16 }} />
        )
      ),
    },
    {
      title: '配置名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
      render: (name: string, record: Config) => (
        <Space>
          <span>{name}</span>
          {record.is_active && <Tag color="green">活跃</Tag>}
        </Space>
      ),
    },
    {
      title: 'API地址',
      dataIndex: 'api_url',
      key: 'api_url',
      ellipsis: true,
      render: (url: string) => (
        <Tooltip title={url}>
          <span>{url}</span>
        </Tooltip>
      ),
    },
    {
      title: 'API密钥',
      dataIndex: 'api_key_masked',
      key: 'api_key',
      width: 150,
      ellipsis: true,
      render: (key: string) => (
        <Tooltip title={key}>
          <span>{key}</span>
        </Tooltip>
      ),
    },
    {
      title: '超时/模式',
      key: 'timeout_mode',
      width: 120,
      render: (_, record: Config) => (
        <span>{record.timeout}s / {record.response_mode}</span>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_, record: Config) => (
        <Space size="small">
          {!record.is_active && (
            <Button
              type="primary"
              size="small"
              onClick={() => handleActivate(record.name)}
            >
              激活
            </Button>
          )}
          <Tooltip title="测试连接">
            <Button
              type="text"
              size="small"
              icon={<ApiOutlined />}
              loading={testingConnection === record.name}
              onClick={() => handleTestConnection(record)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          {record.name !== 'default' && (
            <Popconfirm
              title="确定删除此配置？"
              onConfirm={() => handleDelete(record.name)}
              okText="确定"
              cancelText="取消"
            >
              <Tooltip title="删除">
                <Button
                  type="text"
                  size="small"
                  danger
                  icon={<DeleteOutlined />}
                />
              </Tooltip>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  const configFormItems = (
    <>
      <Form.Item
        name="name"
        label="配置名称"
        rules={[
          { required: true, message: '请输入配置名称' },
          { pattern: /^[a-zA-Z0-9_\u4e00-\u9fff\-\.]+$/, message: '只能包含字母、数字、中文、下划线、连字符和点号' }
        ]}
      >
        <Input placeholder="请输入配置名称" disabled={!!editingConfig} />
      </Form.Item>

      <Form.Item
        name="api_url"
        label="API地址"
        rules={[
          { required: true, message: '请输入API地址' },
          { type: 'url', message: '请输入有效的URL' }
        ]}
      >
        <Input placeholder="https://api.dify.ai/v1" />
      </Form.Item>

      <Form.Item
        name="api_key"
        label="API密钥"
        rules={[
          { required: !editingConfig, message: '请输入API密钥' },
          { min: 10, message: 'API密钥长度不能少于10个字符' }
        ]}
      >
        <Input.Password placeholder={editingConfig ? "留空表示不修改" : "请输入API密钥"} />
      </Form.Item>

      <Form.Item name="user_id" label="用户ID" initialValue="test_user">
        <Input placeholder="test_user" />
      </Form.Item>

      <Form.Item name="timeout" label="超时时间(秒)" initialValue={120}>
        <InputNumber min={10} max={300} style={{ width: '100%' }} />
      </Form.Item>

      <Form.Item name="response_mode" label="响应模式" initialValue="streaming">
        <Select>
          <Option value="streaming">流式</Option>
          <Option value="blocking">阻塞</Option>
        </Select>
      </Form.Item>

      <Form.Item name="log_level" label="日志级别" initialValue="INFO">
        <Select>
          <Option value="DEBUG">DEBUG</Option>
          <Option value="INFO">INFO</Option>
          <Option value="WARNING">WARNING</Option>
          <Option value="ERROR">ERROR</Option>
        </Select>
      </Form.Item>

      <Form.Item name="output_dir" label="输出目录">
        <Input placeholder="留空使用默认目录" />
      </Form.Item>

      <Form.Item name="include_timestamp" label="包含时间戳" valuePropName="checked" initialValue={true}>
        <Switch />
      </Form.Item>
    </>
  );

  return (
    <Card
      title={`配置管理 (${configs.length}个)`}
      extra={
        <Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setShowCreateModal(true)}
          >
            新建配置
          </Button>
          {selectedRowKeys.length > 0 && (
            <Popconfirm
              title={`确定删除选中的 ${selectedRowKeys.length} 个配置？`}
              onConfirm={handleBatchDelete}
              okText="确定"
              cancelText="取消"
            >
              <Button
                danger
                icon={<DeleteOutlined />}
              >
                批量删除 ({selectedRowKeys.length})
              </Button>
            </Popconfirm>
          )}
        </Space>
      }
    >
      <Spin spinning={loading}>
        <Table
          columns={columns}
          dataSource={configs}
          rowKey="name"
          rowSelection={rowSelection}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 个`,
          }}
          locale={{ emptyText: '暂无配置' }}
          size="small"
        />
      </Spin>

      {/* 创建配置模态框 */}
      <Modal
        title="创建配置"
        open={showCreateModal}
        onCancel={() => {
          setShowCreateModal(false);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreate}
        >
          {configFormItems}
        </Form>
      </Modal>

      {/* 编辑配置模态框 */}
      <Modal
        title="编辑配置"
        open={showEditModal}
        onCancel={() => {
          setShowEditModal(false);
          setEditingConfig(null);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleUpdate}
        >
          {configFormItems}
        </Form>
      </Modal>
    </Card>
  );
};

export default ConfigPanel;