import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Form,
  Input,
  InputNumber,
  Modal,
  message,
  Popconfirm,
  Space,
  Upload,
  Tooltip,
  Tag,
  Spin,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  UploadOutlined,
  DownloadOutlined,
  ClearOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { UploadProps } from 'antd/es/upload';
import { testCaseApi } from '../services/api';
import type { TestCase, TestCaseCreate, TestCaseUpdate } from '../types';

const { TextArea } = Input;

interface TestCasePanelProps {
  onCasesChange?: (count: number) => void;
}

const TestCasePanel: React.FC<TestCasePanelProps> = ({ onCasesChange }) => {
  const [cases, setCases] = useState<TestCase[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingCase, setEditingCase] = useState<TestCase | null>(null);
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([]);
  const [form] = Form.useForm();

  // 加载测试用例列表
  const loadTestCases = async () => {
    setLoading(true);
    try {
      const response = await testCaseApi.getTestCases();
      if (response.data.success) {
        const caseList = response.data.data || [];
        setCases(caseList);
        onCasesChange?.(caseList.length);
      } else {
        message.error(response.data.message);
      }
    } catch (error) {
      message.error('加载测试用例失败');
      console.error('Load test cases error:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTestCases();
  }, []);

  // 创建测试用例
  const handleCreate = async (values: TestCaseCreate) => {
    try {
      const response = await testCaseApi.createTestCase(values);
      if (response.data.success) {
        message.success('测试用例创建成功');
        setShowCreateModal(false);
        form.resetFields();
        loadTestCases();
      } else {
        message.error(response.data.message);
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '创建测试用例失败');
    }
  };

  // 更新测试用例
  const handleUpdate = async (values: TestCaseUpdate) => {
    if (!editingCase) return;
    
    try {
      const response = await testCaseApi.updateTestCase(editingCase.id, values);
      if (response.data.success) {
        message.success('测试用例更新成功');
        setShowEditModal(false);
        setEditingCase(null);
        form.resetFields();
        loadTestCases();
      } else {
        message.error(response.data.message);
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '更新测试用例失败');
    }
  };

  // 删除测试用例
  const handleDelete = async (id: string) => {
    try {
      const response = await testCaseApi.deleteTestCase(id);
      if (response.data.success) {
        message.success('测试用例删除成功');
        loadTestCases();
      } else {
        message.error(response.data.message);
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除测试用例失败');
    }
  };

  // 批量删除测试用例
  const handleBatchDelete = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要删除的测试用例');
      return;
    }

    try {
      // 并发删除所有选中的测试用例
      const deletePromises = selectedRowKeys.map(id => testCaseApi.deleteTestCase(id));
      const results = await Promise.allSettled(deletePromises);
      
      const successCount = results.filter(result => 
        result.status === 'fulfilled' && result.value.data.success
      ).length;
      
      if (successCount === selectedRowKeys.length) {
        message.success(`成功删除 ${successCount} 条测试用例`);
      } else {
        message.warning(`删除了 ${successCount}/${selectedRowKeys.length} 条测试用例`);
      }
      
      setSelectedRowKeys([]);
      loadTestCases();
    } catch (error: any) {
      message.error('批量删除失败');
      console.error('Batch delete error:', error);
    }
  };

  // 清空测试用例
  const handleClear = async () => {
    try {
      const response = await testCaseApi.clearTestCases();
      if (response.data.success) {
        message.success('测试用例已清空');
        loadTestCases();
      } else {
        message.error(response.data.message);
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '清空测试用例失败');
    }
  };

  // 编辑测试用例
  const handleEdit = (testCase: TestCase) => {
    setEditingCase(testCase);
    form.setFieldsValue({
      conversation_id: testCase.conversation_id,
      round: testCase.round,
      user_question: testCase.user_question,
      expected_response: testCase.expected_response,
      inputs: testCase.inputs,
    });
    setShowEditModal(true);
  };

  // 下载模板
  const handleDownloadTemplate = async () => {
    try {
      const response = await testCaseApi.downloadTemplate();
      
      // 创建下载链接
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', '测试用例模板.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      message.success('模板下载成功');
    } catch (error) {
      message.error('下载模板失败');
      console.error('Download template error:', error);
    }
  };

  // 文件上传配置
  const uploadProps: UploadProps = {
    name: 'file',
    accept: '.xlsx,.xls,.csv',
    showUploadList: false,
    beforeUpload: (file) => {
      const isValidType = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
                         file.type === 'application/vnd.ms-excel' ||
                         file.type === 'text/csv' ||
                         file.name.endsWith('.xlsx') ||
                         file.name.endsWith('.xls') ||
                         file.name.endsWith('.csv');
      
      if (!isValidType) {
        message.error('只支持 Excel 和 CSV 文件');
        return false;
      }

      const isLt10M = file.size / 1024 / 1024 < 10;
      if (!isLt10M) {
        message.error('文件大小不能超过 10MB');
        return false;
      }

      return true;
    },
    customRequest: async ({ file, onSuccess, onError }) => {
      setUploading(true);
      try {
        const response = await testCaseApi.uploadFile(file as File);
        if (response.data.success) {
          message.success(`成功上传 ${response.data.data?.cases_count} 条测试用例`);
          loadTestCases();
          onSuccess?.(response.data);
        } else {
          message.error(response.data.message);
          onError?.(new Error(response.data.message));
        }
      } catch (error: any) {
        const errorMsg = error.response?.data?.detail || '文件上传失败';
        message.error(errorMsg);
        onError?.(error);
      } finally {
        setUploading(false);
      }
    },
  };

  // 行选择配置
  const rowSelection = {
    selectedRowKeys,
    onChange: (newSelectedRowKeys: React.Key[]) => {
      setSelectedRowKeys(newSelectedRowKeys as string[]);
    },
    onSelectAll: (selected: boolean, _selectedRows: TestCase[], _changeRows: TestCase[]) => {
      if (selected) {
        setSelectedRowKeys(cases.map(item => item.id));
      } else {
        setSelectedRowKeys([]);
      }
    },
  };

  // 表格列定义
  const columns: ColumnsType<TestCase> = [
    {
      title: '对话ID',
      dataIndex: 'conversation_id',
      key: 'conversation_id',
      width: 120,
      ellipsis: true,
    },
    {
      title: '轮次',
      dataIndex: 'round',
      key: 'round',
      width: 60,
      align: 'center',
    },
    {
      title: '用户问题',
      dataIndex: 'user_question',
      key: 'user_question',
      ellipsis: true,
      render: (text: string) => (
        <Tooltip title={text}>
          <span>{text}</span>
        </Tooltip>
      ),
    },
    {
      title: '期待回复',
      dataIndex: 'expected_response',
      key: 'expected_response',
      width: 200,
      ellipsis: true,
      render: (text: string) => (
        text ? (
          <Tooltip title={text}>
            <span>{text}</span>
          </Tooltip>
        ) : (
          <Tag color="default">无</Tag>
        )
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="编辑">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确定删除此测试用例？"
            onConfirm={() => handleDelete(record.id)}
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
        </Space>
      ),
    },
  ];

  const testCaseFormItems = (
    <>
      <Form.Item
        name="conversation_id"
        label="对话ID"
        rules={[
          { required: true, message: '请输入对话ID' },
          { pattern: /^[a-zA-Z0-9_\u4e00-\u9fff\-]+$/, message: '只能包含字母、数字、中文、下划线和连字符' }
        ]}
      >
        <Input placeholder="请输入对话ID" />
      </Form.Item>

      <Form.Item
        name="round"
        label="轮次"
        rules={[{ required: true, message: '请输入轮次' }]}
        initialValue={1}
      >
        <InputNumber min={1} style={{ width: '100%' }} />
      </Form.Item>

      <Form.Item
        name="user_question"
        label="用户问题"
        rules={[{ required: true, message: '请输入用户问题' }]}
      >
        <TextArea
          rows={3}
          placeholder="请输入用户问题"
          maxLength={10000}
          showCount
        />
      </Form.Item>

      <Form.Item name="expected_response" label="期待回复">
        <TextArea
          rows={3}
          placeholder="请输入期待的回复内容（可选）"
          maxLength={50000}
          showCount
        />
      </Form.Item>

      <Form.Item name="inputs" label="额外参数">
        <TextArea
          rows={2}
          placeholder="请输入JSON格式的额外参数（可选）"
        />
      </Form.Item>
    </>
  );

  return (
    <Card
      title={`测试用例管理 (${cases.length}条)`}
      extra={
        <Space>
          <Tooltip title="下载模板">
            <Button
              icon={<DownloadOutlined />}
              onClick={handleDownloadTemplate}
            >
              模板
            </Button>
          </Tooltip>
          <Upload {...uploadProps}>
            <Button
              icon={<UploadOutlined />}
              loading={uploading}
            >
              上传文件
            </Button>
          </Upload>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setShowCreateModal(true)}
          >
            添加用例
          </Button>
          {selectedRowKeys.length > 0 && (
            <Popconfirm
              title={`确定删除选中的 ${selectedRowKeys.length} 条测试用例？`}
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
          {cases.length > 0 && (
            <Popconfirm
              title="确定清空所有测试用例？"
              onConfirm={handleClear}
              okText="确定"
              cancelText="取消"
            >
              <Button
                danger
                icon={<ClearOutlined />}
              >
                清空
              </Button>
            </Popconfirm>
          )}
        </Space>
      }
    >
      <Spin spinning={loading}>
        <Table
          columns={columns}
          dataSource={cases}
          rowKey="id"
          rowSelection={rowSelection}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
          locale={{ emptyText: '暂无测试用例' }}
          size="small"
        />
      </Spin>

      {/* 创建测试用例模态框 */}
      <Modal
        title="添加测试用例"
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
          {testCaseFormItems}
        </Form>
      </Modal>

      {/* 编辑测试用例模态框 */}
      <Modal
        title="编辑测试用例"
        open={showEditModal}
        onCancel={() => {
          setShowEditModal(false);
          setEditingCase(null);
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
          {testCaseFormItems}
        </Form>
      </Modal>
    </Card>
  );
};

export default TestCasePanel;