import type { ApiError } from "./client"
import useCustomToast from "./hooks/useCustomToast"

export const emailPattern = {
  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
  message: "Invalid email address",
}

export const namePattern = {
  value: /^[A-Za-z\s\u00C0-\u017F]{1,30}$/,
  message: "Invalid name",
}

export const passwordRules = (isRequired = true) => {
  const rules: any = {
    minLength: {
      value: 8,
      message: "Password must be at least 8 characters",
    },
  }

  if (isRequired) {
    rules.required = "Password is required"
  }

  return rules
}

export const confirmPasswordRules = (
  getValues: () => any,
  isRequired = true,
) => {
  const rules: any = {
    validate: (value: string) => {
      const password = getValues().password || getValues().new_password
      return value === password ? true : "The passwords do not match"
    },
  }

  if (isRequired) {
    rules.required = "Password confirmation is required"
  }

  return rules
}

export const handleError = (err: ApiError) => {
  const { showErrorToast } = useCustomToast()
  const errDetail = (err.body as any)?.detail
  let errorMessage = errDetail || "Something went wrong."
  if (Array.isArray(errDetail) && errDetail.length > 0) {
    errorMessage = errDetail[0].msg
  }
  showErrorToast(errorMessage)
}

/**
 * 生成全局唯一标识符 (GUID/UUID)
 * 优先使用现代浏览器的crypto.randomUUID()，降级使用自定义实现
 * 
 * @returns {string} 标准UUID v4格式的GUID字符串
 * 
 * @example
 * ```typescript
 * const guid = generateGUID();
 * console.log(guid); // "550e8400-e29b-41d4-a716-446655440000"
 * ```
 */
export function generateGUID(): string {
  // 优先使用现代浏览器的crypto.randomUUID()
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  
  // 降级方案：使用自定义实现
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

/**
 * 生成简化的唯一标识符（不包含连字符）
 * 
 * @returns {string} 32位十六进制字符串
 * 
 * @example
 * ```typescript
 * const simpleId = generateSimpleGUID();
 * console.log(simpleId); // "550e8400e29b41d4a716446655440000"
 * ```
 */
export function generateSimpleGUID(): string {
  return generateGUID().replace(/-/g, '');
}

/**
 * 生成带前缀的GUID
 * 
 * @param {string} prefix - 前缀字符串
 * @returns {string} 带前缀的GUID
 * 
 * @example
 * ```typescript
 * const prefixedId = generatePrefixedGUID('new');
 * console.log(prefixedId); // "new-550e8400-e29b-41d4-a716-446655440000"
 * ```
 */
export function generatePrefixedGUID(prefix: string): string {
  return `${prefix}-${generateGUID()}`;
}
