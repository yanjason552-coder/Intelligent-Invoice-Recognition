/**
 * 统一API对象类型定义
 * 对应后端的UnifiedRequest和UnifiedResponse
 */

// ==================== API 配置 ====================
export const API_CONFIG = {
  // API 基础 URL
  BASE_URL: 'http://localhost:8000/api/v1',
  
}

// 获取完整的 API URL
export const getApiUrl = (endpoint: string): string => {
  return `${API_CONFIG.BASE_URL}${endpoint}`
}

// 获取带认证的请求头
export const getAuthHeaders = (): Record<string, string> => {
  const token = localStorage.getItem('access_token')
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  }
}

// 统一的API传入参数对象
export interface UnifiedRequest<T = any> {
  // 基础信息
  action: string;  // 操作类型：login, register, create, read, update, delete, list
  module: string;  // 模块名称：user, item, order, etc.
  
  // 数据字段
  data?: T;  // 主要数据
  params?: Record<string, any>;  // 额外参数
  filters?: Record<string, any>;  // 过滤条件
  sort?: Record<string, 'asc' | 'desc'>;  // 排序条件
  
  // 分页信息
  page?: number;
  limit?: number;
  search?: string;  // 搜索关键词
  
  // 安全信息
  timestamp?: string;  // 请求时间戳
  signature?: string;  // 请求签名（可选）
  
  // 元数据
  request_id?: string;  // 请求ID
  client_info?: Record<string, any>;  // 客户端信息
}

// 统一的API返回参数对象
export interface UnifiedResponse<T = any> {
  // 基础状态
  success: boolean;  // 操作是否成功
  code: number;  // HTTP状态码
  
  // 数据内容
  data?: T;  // 主要数据
  message?: string;  // 响应消息
  error_code?: string;  // 错误代码
  
  // 分页信息（当返回列表时）
  pagination?: PaginationInfo;  // 分页信息
  
  // 元数据
  timestamp?: string;  // 响应时间戳
  request_id?: string;  // 请求ID
  duration?: number;  // 处理耗时（毫秒）
  
  // 调试信息（开发环境）
  debug?: Record<string, any>;  // 调试信息
}

// 分页信息对象
export interface PaginationInfo {
  page: number;  // 当前页码
  limit: number;  // 每页数量
  total: number;  // 总数量
  total_pages: number;  // 总页数
  has_next: boolean;  // 是否有下一页
  has_prev: boolean;  // 是否有上一页
}

// 错误信息对象
export interface ErrorInfo {
  code: string;  // 错误代码
  message: string;  // 错误消息
  details?: Record<string, any>;  // 错误详情
  field?: string;  // 错误字段（表单验证错误时）
}

// 用户数据对象
export interface UserData {
  id: string;
  email: string;
  full_name?: string;
  is_active?: boolean;
  is_superuser?: boolean;
}

// 项目数据对象
export interface ItemData {
  id: string;
  title: string;
  description?: string;
  owner_id: string;
}

// 物料类别明细数据对象
export interface MaterialClassDData {
  materialClassDId: string;
  materialClassId: string;
  featureId: string;
  featureCode: string;
  featureValue: string;
  position: number;
  remark?: string;
  creator: string;
  createDate: string;
  modifierLast?: string;
  modifyDateLast?: string;
  approveStatus: string;
  approver?: string;
  approveDate?: string;
}

// 物料类别数据对象
export interface MaterialClassData {
  materialClassId: string;
  materialClassPId: string;
  classCode: string;
  classDesc: string;
  remark?: string;
  creator: string;
  createDate: string;
  modifierLast?: string;
  modifyDateLast?: string;
  approveStatus: string;
  approver?: string;
  approveDate?: string;
  materialClassDList: MaterialClassDData[];
}

// 定义具体的请求类型别名
export type MaterialClassRequest = UnifiedRequest<MaterialClassData>;
export type MaterialClassListRequest = UnifiedRequest<Record<string, any>>;  // 列表查询通常不需要具体数据
export type MaterialClassDeleteRequest = UnifiedRequest<{materialClassId: string}>;  // 删除请求只需要ID

// 登录响应数据
export interface LoginData {
  access_token: string;
  token_type: string;
  user: UserData;
}

// 分页响应数据
export interface PaginatedData<T = any> {
  data: T[];
  pagination: PaginationInfo;
}

// 预定义的请求构建器
export class UnifiedRequestBuilder {
  private request: Partial<UnifiedRequest> = {};

  constructor(module: string, action: string) {
    this.request.module = module;
    this.request.action = action;
    this.request.timestamp = new Date().toISOString();
    this.request.request_id = this.generateRequestId();
  }

  // 设置数据
  setData(data: Record<string, any>): this {
    this.request.data = data;
    return this;
  }

  // 设置参数
  setParams(params: Record<string, any>): this {
    this.request.params = params;
    return this;
  }

  // 设置过滤器
  setFilters(filters: Record<string, any>): this {
    this.request.filters = filters;
    return this;
  }

  // 设置排序
  setSort(sort: Record<string, 'asc' | 'desc'>): this {
    this.request.sort = sort;
    return this;
  }

  // 设置分页
  setPagination(page: number, limit: number): this {
    this.request.page = page;
    this.request.limit = limit;
    return this;
  }

  // 设置搜索
  setSearch(search: string): this {
    this.request.search = search;
    return this;
  }

  // 设置客户端信息
  setClientInfo(clientInfo: Record<string, any>): this {
    this.request.client_info = clientInfo;
    return this;
  }

  // 构建请求对象
  build(): UnifiedRequest {
    return this.request as UnifiedRequest;
  }

  // 生成请求ID
  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

// 便捷的请求构建函数
export const createUserRequest = (action: string) => 
  new UnifiedRequestBuilder('user', action);

export const createItemRequest = (action: string) => 
  new UnifiedRequestBuilder('item', action);

// 统一的API客户端
export class UnifiedApiClient {
  private baseUrl: string;
  private accessToken: string | null = null;

  constructor(baseUrl: string = '/api/v1') {
    this.baseUrl = baseUrl;
    this.accessToken = localStorage.getItem('access_token');
  }

  // 设置访问令牌
  setAccessToken(token: string) {
    this.accessToken = token;
    localStorage.setItem('access_token', token);
  }

  // 清除访问令牌
  clearAccessToken() {
    this.accessToken = null;
    localStorage.removeItem('access_token');
  }

  // 发送统一请求
  async sendRequest<T = any>(request: UnifiedRequest): Promise<UnifiedResponse<T>> {
    const url = `${this.baseUrl}/unified-v2/api`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(request),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.message || '请求失败');
      }

      return result;
    } catch (error) {
      console.error('统一API请求错误:', error);
      throw error;
    }
  }

  // 用户登录
  async login(email: string, password: string): Promise<UnifiedResponse<LoginData>> {
    const request = createUserRequest('login')
      .setData({ email, password })
      .build();

    const response = await this.sendRequest<LoginData>(request);
    
    if (response.success && response.data?.access_token) {
      this.setAccessToken(response.data.access_token);
    }

    return response;
  }

  // 用户注册
  async register(email: string, password: string, full_name?: string): Promise<UnifiedResponse<UserData>> {
    const request = createUserRequest('register')
      .setData({ email, password, full_name })
      .build();

    return this.sendRequest<UserData>(request);
  }

  // 获取用户列表
  async getUserList(
    page: number = 1, 
    limit: number = 20, 
    filters?: Record<string, any>,
    sort?: Record<string, 'asc' | 'desc'>
  ): Promise<UnifiedResponse<PaginatedData<UserData>>> {
    const request = createUserRequest('list')
      .setPagination(page, limit)
      .setFilters(filters || {})
      .setSort(sort || {})
      .build();

    return this.sendRequest<PaginatedData<UserData>>(request);
  }

  // 创建项目
  async createItem(title: string, description?: string): Promise<UnifiedResponse<ItemData>> {
    const request = createItemRequest('create')
      .setData({ title, description })
      .build();

    return this.sendRequest<ItemData>(request);
  }

  // 获取项目列表
  async getItemList(
    page: number = 1, 
    limit: number = 20, 
    filters?: Record<string, any>,
    sort?: Record<string, 'asc' | 'desc'>,
    search?: string
  ): Promise<UnifiedResponse<PaginatedData<ItemData>>> {
    const request = createItemRequest('list')
      .setPagination(page, limit)
      .setFilters(filters || {})
      .setSort(sort || {})
      .setSearch(search || '')
      .build();

    return this.sendRequest<PaginatedData<ItemData>>(request);
  }

  // 读取项目
  async getItem(id: string): Promise<UnifiedResponse<ItemData>> {
    const request = createItemRequest('read')
      .setData({ id })
      .build();

    return this.sendRequest<ItemData>(request);
  }

  // 更新项目
  async updateItem(id: string, title?: string, description?: string): Promise<UnifiedResponse<ItemData>> {
    const request = createItemRequest('update')
      .setData({ id, title, description })
      .build();

    return this.sendRequest<ItemData>(request);
  }

  // 删除项目
  async deleteItem(id: string): Promise<UnifiedResponse<void>> {
    const request = createItemRequest('delete')
      .setData({ id })
      .build();

    return this.sendRequest<void>(request);
  }
}

// 创建全局API客户端实例
export const unifiedApiClient = new UnifiedApiClient();

// React Hook示例
export function useUnifiedApi() {
  const login = async (email: string, password: string) => {
    try {
      const response = await unifiedApiClient.login(email, password);
      if (response.success) {
        console.log('登录成功:', response.message);
        return response.data;
      } else {
        console.error('登录失败:', response.message);
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('登录异常:', error);
      throw error;
    }
  };

  const register = async (email: string, password: string, full_name?: string) => {
    try {
      const response = await unifiedApiClient.register(email, password, full_name);
      if (response.success) {
        console.log('注册成功:', response.message);
        return response.data;
      } else {
        console.error('注册失败:', response.message);
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('注册异常:', error);
      throw error;
    }
  };

  const getUserList = async (page: number = 1, limit: number = 20) => {
    try {
      const response = await unifiedApiClient.getUserList(page, limit);
      if (response.success) {
        return {
          users: response.data?.data || [],
          pagination: response.data?.pagination,
        };
      } else {
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('获取用户列表异常:', error);
      throw error;
    }
  };

  const createItem = async (title: string, description?: string) => {
    try {
      const response = await unifiedApiClient.createItem(title, description);
      if (response.success) {
        console.log('项目创建成功:', response.message);
        return response.data;
      } else {
        console.error('项目创建失败:', response.message);
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('项目创建异常:', error);
      throw error;
    }
  };

  const getItemList = async (page: number = 1, limit: number = 20) => {
    try {
      const response = await unifiedApiClient.getItemList(page, limit);
      if (response.success) {
        return {
          items: response.data?.data || [],
          pagination: response.data?.pagination,
        };
      } else {
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('获取项目列表异常:', error);
      throw error;
    }
  };

  const updateItem = async (id: string, title?: string, description?: string) => {
    try {
      const response = await unifiedApiClient.updateItem(id, title, description);
      if (response.success) {
        console.log('项目更新成功:', response.message);
        return response.data;
      } else {
        console.error('项目更新失败:', response.message);
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('项目更新异常:', error);
      throw error;
    }
  };

  const deleteItem = async (id: string) => {
    try {
      const response = await unifiedApiClient.deleteItem(id);
      if (response.success) {
        console.log('项目删除成功:', response.message);
        return true;
      } else {
        console.error('项目删除失败:', response.message);
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('项目删除异常:', error);
      throw error;
    }
  };

  return {
    login,
    register,
    getUserList,
    createItem,
    getItemList,
    updateItem,
    deleteItem,
  };
} 