import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'

interface Toast {
  id: string
  title: string
  description: string
  type: 'success' | 'error' | 'info'
}

interface ToastContextType {
  toasts: Toast[]
  addToast: (toast: Omit<Toast, 'id'>) => void
  removeToast: (id: string) => void
}

const ToastContext = createContext<ToastContextType | undefined>(undefined)

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}

function ToastProviderComponent({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  // 添加CSS动画（仅在客户端执行一次）
  useEffect(() => {
    if (typeof document !== 'undefined') {
      const styleId = 'toast-animation-style'
      if (!document.getElementById(styleId)) {
        const style = document.createElement('style')
        style.id = styleId
        style.textContent = `
          @keyframes slideIn {
            from {
              transform: translateX(100%);
              opacity: 0;
            }
            to {
              transform: translateX(0);
              opacity: 1;
            }
          }
        `
        document.head.appendChild(style)
      }
    }
  }, [])

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id))
  }, [])

  const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substr(2, 9)
    const newToast = { ...toast, id }
    
    setToasts(prev => [...prev, newToast])
    
    // 3秒后自动移除
    setTimeout(() => {
      removeToast(id)
    }, 3000)
  }, [removeToast])

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </ToastContext.Provider>
  )
}

const ToastContainer: React.FC<{ toasts: Toast[], removeToast: (id: string) => void }> = ({ toasts, removeToast }) => {
  return (
    <div style={{
      position: 'fixed',
      bottom: '20px',
      right: '20px',
      zIndex: 9999,
      display: 'flex',
      flexDirection: 'column',
      gap: '10px',
      pointerEvents: 'none'
    }}>
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} removeToast={removeToast} />
      ))}
    </div>
  )
}

const ToastItem: React.FC<{ toast: Toast, removeToast: (id: string) => void }> = ({ toast, removeToast }) => {
  const getToastStyle = () => {
    const baseStyle: React.CSSProperties = {
      padding: '12px 16px',
      borderRadius: '6px',
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
      minWidth: '300px',
      maxWidth: '400px',
      color: 'white',
      fontSize: '14px',
      lineHeight: '1.4',
      pointerEvents: 'auto',
      animation: 'slideIn 0.3s ease-out',
      display: 'flex',
      alignItems: 'flex-start',
      gap: '8px'
    }

    switch (toast.type) {
      case 'success':
        return { ...baseStyle, backgroundColor: '#10b981' }
      case 'error':
        return { ...baseStyle, backgroundColor: '#ef4444' }
      case 'info':
        return { ...baseStyle, backgroundColor: '#3b82f6' }
      default:
        return { ...baseStyle, backgroundColor: '#6b7280' }
    }
  }

  const getIcon = () => {
    switch (toast.type) {
      case 'success':
        return '✅'
      case 'error':
        return '❌'
      case 'info':
        return 'ℹ️'
      default:
        return '💬'
    }
  }

  return (
    <div style={getToastStyle()}>
      <span style={{ fontSize: '16px', flexShrink: 0 }}>{getIcon()}</span>
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
          {toast.title}
        </div>
        <div style={{ opacity: 0.9 }}>
          {toast.description}
        </div>
      </div>
      <button
        onClick={() => removeToast(toast.id)}
        style={{
          background: 'none',
          border: 'none',
          color: 'white',
          fontSize: '18px',
          cursor: 'pointer',
          padding: '0',
          marginLeft: '8px',
          opacity: 0.7,
          flexShrink: 0
        }}
        onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
        onMouseLeave={(e) => e.currentTarget.style.opacity = '0.7'}
      >
        ×
      </button>
    </div>
  )
}

// 明确导出
export const ToastProvider = ToastProviderComponent
