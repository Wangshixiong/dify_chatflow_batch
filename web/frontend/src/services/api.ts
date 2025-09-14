// API 服务封装
import axios from 'axios';
import type { AxiosResponse } from 'axios';
import type {
  Config,
  ConfigCreate,
  ConfigUpdate,
  TestCase,
  TestCaseCreate,
  TestCaseUpdate,
  ApiResponse,
  ConnectionTestRequest,
  ConnectionTestResponse,
  FileUploadResponse
} from '../types';

// 创建 axios 实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? '' : 'http://127.0.0.1:8080'),
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// 配置管理 API
export const configApi = {
  // 获取配置列表
  getConfigs: (): Promise<AxiosResponse<ApiResponse<Config[]>>> =>
    api.get('/api/configs'),

  // 创建配置
  createConfig: (config: ConfigCreate): Promise<AxiosResponse<ApiResponse>> =>
    api.post('/api/configs', config),

  // 更新配置
  updateConfig: (name: string, config: ConfigUpdate): Promise<AxiosResponse<ApiResponse>> =>
    api.put(`/api/configs/${name}`, config),

  // 删除配置
  deleteConfig: (name: string): Promise<AxiosResponse<ApiResponse>> =>
    api.delete(`/api/configs/${name}`),

  // 激活配置
  activateConfig: (name: string): Promise<AxiosResponse<ApiResponse>> =>
    api.post(`/api/configs/${name}/activate`),

  // 测试连接
  testConnection: (request: ConnectionTestRequest): Promise<AxiosResponse<ConnectionTestResponse>> =>
    api.post('/api/configs/test', request),

  // 测试已保存配置的连接
  testConfigConnection: (name: string): Promise<AxiosResponse<ConnectionTestResponse>> =>
    api.post(`/api/configs/${name}/test`),
};

// 测试用例管理 API
export const testCaseApi = {
  // 获取测试用例列表
  getTestCases: (): Promise<AxiosResponse<ApiResponse<TestCase[]>>> =>
    api.get('/api/testcases'),

  // 创建测试用例
  createTestCase: (testCase: TestCaseCreate): Promise<AxiosResponse<ApiResponse>> =>
    api.post('/api/testcases', testCase),

  // 更新测试用例
  updateTestCase: (id: string, testCase: TestCaseUpdate): Promise<AxiosResponse<ApiResponse>> =>
    api.put(`/api/testcases/${id}`, testCase),

  // 删除测试用例
  deleteTestCase: (id: string): Promise<AxiosResponse<ApiResponse>> =>
    api.delete(`/api/testcases/${id}`),

  // 清空测试用例
  clearTestCases: (): Promise<AxiosResponse<ApiResponse>> =>
    api.delete('/api/testcases'),

  // 上传测试用例文件
  uploadFile: (file: File): Promise<AxiosResponse<ApiResponse<FileUploadResponse>>> => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/testcases/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  // 下载模板
  downloadTemplate: (): Promise<AxiosResponse<Blob>> =>
    api.get('/api/testcases/template', {
      responseType: 'blob',
    }),
};

// 测试执行 API
export const executionApi = {
  // 开始测试
  startTest: (): Promise<AxiosResponse<ApiResponse>> =>
    api.post('/api/test/start'),

  // 暂停测试
  pauseTest: (): Promise<AxiosResponse<ApiResponse>> =>
    api.post('/api/test/pause'),

  // 恢复测试
  resumeTest: (): Promise<AxiosResponse<ApiResponse>> =>
    api.post('/api/test/resume'),

  // 停止测试
  stopTest: (): Promise<AxiosResponse<ApiResponse>> =>
    api.post('/api/test/stop'),

  // 获取测试状态
  getTestStatus: (): Promise<AxiosResponse<ApiResponse>> =>
    api.get('/api/test/status'),
};

// 系统 API
export const systemApi = {
  // 健康检查
  healthCheck: (): Promise<AxiosResponse<any>> =>
    api.get('/api/health'),
};

export default api;