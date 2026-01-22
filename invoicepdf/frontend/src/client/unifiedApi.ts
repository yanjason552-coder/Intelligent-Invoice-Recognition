/**
 * 统一API调用示例
 * 展示如何使用统一的传入参数和返回参数格式
 */

// 统一的API响应类型
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error_code?: string;
  timestamp?: string;
}

// 分页响应类型
export interface PaginatedResponse<T = any> extends ApiResponse<T[]> {
  count: number;
  page?: number;
  limit?: number;
  total_pages?: number;
}

// 统一的API请求类型
export interface ApiRequest {
  data?: any;
  params?: Record<string, any>;
  filters?: Record<string, any>;
  sort?: Record<string, 'asc' | 'desc'>;
  timestamp?: string;
}

// 分页请求类型
export interface PaginatedRequest {
  page: number;
  limit: number;
  filters?: Record<string, any>;
  sort?: Record<string, 'asc' | 'desc'>;
  search?: string;
  timestamp?: string;
}

// 用户请求类型
export interface UserRequest {
  action: 'login' | 'register' | 'update' | 'delete' | 'list';
  email?: string;
  password?: string;
  full_name?: string;
  is_active?: boolean;
  is_superuser?: boolean;
  filters?: Record<string, any>;
  pagination?: PaginatedRequest;
  timestamp?: string;
}

// 项目请求类型
export interface ItemRequest {
  action: 'create' | 'read' | 'update' | 'delete' | 'list';
  id?: string;
  title?: string;
  description?: string;
  owner_id?: string;
  filters?: Record<string, any>;
  pagination?: PaginatedRequest;
  timestamp?: string;
}

// 通用CRUD请求类型
export interface CrudRequest {
  action: 'create' | 'read' | 'update' | 'delete' | 'list';
  data?: any;
  id?: string;
  filters?: Record<string, any>;
  pagination?: PaginatedRequest;
  timestamp?: string;
}

// 统一API客户端
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

  // 通用请求方法
  private async request<T>(
    endpoint: string,
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'POST',
    data?: any
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    const requestData = {
      ...data,
      timestamp: new Date().toISOString(),
    };

    try {
      const response = await fetch(url, {
        method,
        headers,
        body: method !== 'GET' ? JSON.stringify(requestData) : undefined,
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.message || '请求失败');
      }

      return result;
    } catch (error) {
      console.error('API请求错误:', error);
      throw error;
    }
  }

  // 用户操作
  async userOperations(request: UserRequest): Promise<ApiResponse> {
    return this.request('/unified/users', 'POST', request);
  }

  // 项目操作
  async itemOperations(request: ItemRequest): Promise<ApiResponse> {
    return this.request('/unified/items', 'POST', request);
  }

  // 通用CRUD操作
  async crudOperations(modelName: string, request: CrudRequest): Promise<ApiResponse> {
    return this.request(`/unified/crud/${modelName}`, 'POST', request);
  }

  // 便捷方法：用户登录
  async login(email: string, password: string): Promise<ApiResponse> {
    const request: UserRequest = {
      action: 'login',
      email,
      password,
      timestamp: new Date().toISOString(),
    };

    const response = await this.userOperations(request);
    
    if (response.success && response.data?.access_token) {
      this.setAccessToken(response.data.access_token);
    }

    return response;
  }

  // 便捷方法：用户注册
  async register(email: string, password: string, full_name?: string): Promise<ApiResponse> {
    const request: UserRequest = {
      action: 'register',
      email,
      password,
      full_name,
      timestamp: new Date().toISOString(),
    };

    return this.userOperations(request);
  }

  // 便捷方法：获取用户列表
  async getUserList(page: number = 1, limit: number = 20, filters?: Record<string, any>): Promise<PaginatedResponse> {
    const request: UserRequest = {
      action: 'list',
      pagination: {
        page,
        limit,
        filters,
        timestamp: new Date().toISOString(),
      },
      timestamp: new Date().toISOString(),
    };

    return this.userOperations(request) as Promise<PaginatedResponse>;
  }

  // 便捷方法：创建项目
  async createItem(title: string, description?: string): Promise<ApiResponse> {
    const request: ItemRequest = {
      action: 'create',
      title,
      description,
      timestamp: new Date().toISOString(),
    };

    return this.itemOperations(request);
  }

  // 便捷方法：获取项目列表
  async getItemList(page: number = 1, limit: number = 20, filters?: Record<string, any>): Promise<PaginatedResponse> {
    const request: ItemRequest = {
      action: 'list',
      pagination: {
        page,
        limit,
        filters,
        timestamp: new Date().toISOString(),
      },
      timestamp: new Date().toISOString(),
    };

    return this.itemOperations(request) as Promise<PaginatedResponse>;
  }

  // 便捷方法：更新项目
  async updateItem(id: string, title?: string, description?: string): Promise<ApiResponse> {
    const request: ItemRequest = {
      action: 'update',
      id,
      title,
      description,
      timestamp: new Date().toISOString(),
    };

    return this.itemOperations(request);
  }

  // 便捷方法：删除项目
  async deleteItem(id: string): Promise<ApiResponse> {
    const request: ItemRequest = {
      action: 'delete',
      id,
      timestamp: new Date().toISOString(),
    };

    return this.itemOperations(request);
  }
}

// 创建全局API客户端实例
export const unifiedApi = new UnifiedApiClient();

// React Hook示例
export function useUnifiedApi() {
  const login = async (email: string, password: string) => {
    try {
      const response = await unifiedApi.login(email, password);
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
      const response = await unifiedApi.register(email, password, full_name);
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
      const response = await unifiedApi.getUserList(page, limit);
      if (response.success) {
        return {
          users: response.data,
          totalCount: response.count,
          currentPage: response.page,
          totalPages: response.total_pages,
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
      const response = await unifiedApi.createItem(title, description);
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
      const response = await unifiedApi.getItemList(page, limit);
      if (response.success) {
        return {
          items: response.data,
          totalCount: response.count,
          currentPage: response.page,
          totalPages: response.total_pages,
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
      const response = await unifiedApi.updateItem(id, title, description);
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
      const response = await unifiedApi.deleteItem(id);
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