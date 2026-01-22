/**
 * {业务模块} API客户端
 * 创建时间：{创建时间}
 * 创建人：{创建人}
 * 描述：{业务模块}相关的API调用方法
 */

import { getApiUrl, getAuthHeaders } from './unifiedTypes'

// =============================================
// 数据类型定义
// =============================================

export interface {实体名} {
  id: string
  {字段1}: string
  {字段2}: string
  {字段3}?: string
  {字段4}: number
  isActive: boolean
  createdAt: string
  updatedAt: string
}

export interface {实体名}Create {
  {字段1}: string
  {字段2}: string
  {字段3}?: string
  {字段4}?: number
  isActive?: boolean
}

export interface {实体名}Update {
  {字段1}?: string
  {字段2}?: string
  {字段3}?: string
  {字段4}?: number
  isActive?: boolean
}

export interface {实体名}ListParams {
  skip?: number
  limit?: number
  isActive?: boolean
  search?: string
}

export interface {实体名}ListResponse {
  data: {实体名}[]
  count: number
  skip: number
  limit: number
}

// =============================================
// API方法定义
// =============================================

export const {业务模块}Api = {
  /**
   * 获取{业务模块}列表
   * @param params 查询参数
   * @returns {业务模块}列表
   */
  getList: async (params?: {实体名}ListParams): Promise<{实体名}[]> => {
    const url = new URL(getApiUrl('/{业务模块}'))
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          url.searchParams.append(key, String(value))
        }
      })
    }
    
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: getAuthHeaders(),
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || '获取{业务模块}列表失败')
    }
    
    return response.json()
  },

  /**
   * 获取{业务模块}总数
   * @param isActive 是否启用
   * @returns 总数
   */
  getCount: async (isActive?: boolean): Promise<number> => {
    const url = new URL(getApiUrl('/{业务模块}/count'))
    
    if (isActive !== undefined) {
      url.searchParams.append('isActive', String(isActive))
    }
    
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: getAuthHeaders(),
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || '获取{业务模块}总数失败')
    }
    
    const data = await response.json()
    return data.count
  },

  /**
   * 根据ID获取{业务模块}
   * @param id {业务模块}ID
   * @returns {业务模块}详情
   */
  getById: async (id: string): Promise<{实体名}> => {
    const url = getApiUrl(`/{业务模块}/${id}`)
    
    const response = await fetch(url, {
      method: 'GET',
      headers: getAuthHeaders(),
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || '获取{业务模块}详情失败')
    }
    
    return response.json()
  },

  /**
   * 创建{业务模块}
   * @param data 创建数据
   * @returns 创建的{业务模块}
   */
  create: async (data: {实体名}Create): Promise<{实体名}> => {
    const url = getApiUrl('/{业务模块}')
    
    const response = await fetch(url, {
      method: 'POST',
      headers: { 
        ...getAuthHeaders(), 
        'Content-Type': 'application/json' 
      },
      body: JSON.stringify(data),
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || '创建{业务模块}失败')
    }
    
    return response.json()
  },

  /**
   * 更新{业务模块}
   * @param id {业务模块}ID
   * @param data 更新数据
   * @returns 更新后的{业务模块}
   */
  update: async (id: string, data: {实体名}Update): Promise<{实体名}> => {
    const url = getApiUrl(`/{业务模块}/${id}`)
    
    const response = await fetch(url, {
      method: 'PUT',
      headers: { 
        ...getAuthHeaders(), 
        'Content-Type': 'application/json' 
      },
      body: JSON.stringify(data),
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || '更新{业务模块}失败')
    }
    
    return response.json()
  },

  /**
   * 删除{业务模块}
   * @param id {业务模块}ID
   */
  delete: async (id: string): Promise<void> => {
    const url = getApiUrl(`/{业务模块}/${id}`)
    
    const response = await fetch(url, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || '删除{业务模块}失败')
    }
  },

  /**
   * 批量删除{业务模块}
   * @param ids {业务模块}ID数组
   */
  batchDelete: async (ids: string[]): Promise<void> => {
    const url = getApiUrl('/{业务模块}/batch-delete')
    
    const response = await fetch(url, {
      method: 'POST',
      headers: { 
        ...getAuthHeaders(), 
        'Content-Type': 'application/json' 
      },
      body: JSON.stringify(ids),
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || '批量删除{业务模块}失败')
    }
  },
}

// =============================================
// 类型导出
// =============================================

export type { {实体名}, {实体名}Create, {实体名}Update, {实体名}ListParams, {实体名}ListResponse }
