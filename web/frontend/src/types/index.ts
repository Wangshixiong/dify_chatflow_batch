// 前端类型定义

export interface Config {
  id: string;
  name: string;
  api_url: string;
  api_key_masked: string;
  user_id: string;
  timeout: number;
  response_mode: 'streaming' | 'blocking';
  log_level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';
  output_dir: string;
  include_timestamp: boolean;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface ConfigCreate {
  name: string;
  api_url: string;
  api_key: string;
  user_id?: string;
  timeout?: number;
  response_mode?: 'streaming' | 'blocking';
  log_level?: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';
  output_dir?: string;
  include_timestamp?: boolean;
}

export interface ConfigUpdate {
  name?: string;
  api_url?: string;
  api_key?: string;
  user_id?: string;
  timeout?: number;
  response_mode?: 'streaming' | 'blocking';
  log_level?: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';
  output_dir?: string;
  include_timestamp?: boolean;
}

export interface TestCase {
  id: string;
  conversation_id: string;
  round: number;
  user_question: string;
  expected_response?: string;
  inputs?: string;
  created_at: string;
  updated_at: string;
}

export interface TestCaseCreate {
  conversation_id: string;
  round: number;
  user_question: string;
  expected_response?: string;
  inputs?: string;
}

export interface TestCaseUpdate {
  conversation_id?: string;
  round?: number;
  user_question?: string;
  expected_response?: string;
  inputs?: string;
}

export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
}

export interface ConnectionTestRequest {
  api_url: string;
  api_key: string;
  timeout?: number;
}

export interface ConnectionTestResponse {
  success: boolean;
  message: string;
  response_time?: number;
}

export interface FileUploadResponse {
  filename: string;
  size: number;
  cases_count: number;
  success: boolean;
  message: string;
}

// UI 状态类型
export interface UIState {
  loading: boolean;
  error: string | null;
}

export interface ConfigPanelState extends UIState {
  configs: Config[];
  activeConfig: string | null;
  editingConfig: Config | null;
  showCreateForm: boolean;
  testingConnection: boolean;
}

export interface TestCasePanelState extends UIState {
  cases: TestCase[];
  uploading: boolean;
  editingCase: TestCase | null;
  showCreateForm: boolean;
}