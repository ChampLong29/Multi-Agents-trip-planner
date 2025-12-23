import axios, { AxiosError } from 'axios'
import type { TripFormData, TripPlanResponse } from '@/types'
import type { StreamingData } from '@/stores/tripStore'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2分钟超时
  headers: {
    'Content-Type': 'application/json'
  }
})

// 当前请求控制器（用于请求去重）
let currentRequestController: AbortController | null = null

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 添加JWT token
    const token = localStorage.getItem('trip_planner_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    console.log('发送请求:', config.method?.toUpperCase(), config.url)
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    console.log('收到响应:', response.status, response.config.url)
    return response
  },
  (error) => {
    console.error('响应错误:', error.response?.status, error.message)
    
    // 处理401错误（token过期）
    if (error.response?.status === 401) {
      // 清除token和用户信息
      localStorage.removeItem('trip_planner_token')
      localStorage.removeItem('trip_planner_user')
      
      // 如果不在登录页，跳转到登录页
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    
    return Promise.reject(error)
  }
)

/**
 * 重试请求（指数退避）
 */
async function retryRequest<T>(
  requestFn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<T> {
  let lastError: any
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await requestFn()
    } catch (error: any) {
      lastError = error
      
      // 如果是取消请求，直接抛出
      if (axios.isCancel(error)) {
        throw error
      }
      
      // 如果是最后一次尝试，抛出错误
      if (attempt === maxRetries) {
        break
      }
      
      // 计算延迟时间（指数退避）
      const delay = baseDelay * Math.pow(2, attempt)
      console.log(`请求失败，${delay}ms后重试 (${attempt + 1}/${maxRetries})...`)
      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }
  
  throw lastError
}

/**
 * 生成旅行计划（同步）
 */
export async function generateTripPlan(formData: TripFormData): Promise<TripPlanResponse> {
  // 取消之前的请求
  if (currentRequestController) {
    currentRequestController.abort()
  }
  
  // 创建新请求控制器
  currentRequestController = new AbortController()
  
  try {
    const response = await retryRequest(
      () => apiClient.post<TripPlanResponse>(
        '/api/trip/plan',
        formData,
        { signal: currentRequestController!.signal }
      ),
      3,
      1000
    )
    
    return response.data
  } catch (error: any) {
    if (axios.isCancel(error)) {
      throw new Error('请求已取消')
    }
    console.error('生成旅行计划失败:', error)
    throw new Error(error.response?.data?.detail || error.message || '生成旅行计划失败')
  } finally {
    currentRequestController = null
  }
}

/**
 * 流式生成旅行计划（SSE）
 */
export async function generateTripPlanStream(
  formData: TripFormData,
  onProgress: (data: StreamingData) => void
): Promise<TripPlanResponse> {
  // 取消之前的请求
  if (currentRequestController) {
    currentRequestController.abort()
  }
  
  // 创建新请求控制器
  currentRequestController = new AbortController()
  
  return new Promise((resolve, reject) => {
    // 使用 fetch 实现 SSE（因为 EventSource 不支持 POST）
    fetch(`${API_BASE_URL}/api/trip/plan/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(formData),
      signal: currentRequestController!.signal
    })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      if (!response.body) {
        throw new Error('响应体为空')
      }
      
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let finalPlan: TripPlanResponse | null = null
      
      try {
        while (true) {
          const { done, value } = await reader.read()
          
          if (done) {
            break
          }
          
          buffer += decoder.decode(value, { stream: true })
          
          // 处理完整的 SSE 消息
          const lines = buffer.split('\n')
          buffer = lines.pop() || '' // 保留不完整的行
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data: StreamingData = JSON.parse(line.slice(6))
                onProgress(data)
                
                if (data.type === 'complete' && data.plan) {
                  finalPlan = {
                    success: true,
                    message: data.message || '旅行计划生成成功',
                    data: data.plan,
                    requires_login: data.requires_login ?? false
                  }
                } else if (data.type === 'error') {
                  reject(new Error(data.message || '生成旅行计划失败'))
                  return
                }
              } catch (error) {
                console.error('解析SSE数据失败:', error, line)
              }
            }
          }
        }
        
        // 处理剩余的 buffer
        if (buffer.startsWith('data: ')) {
          try {
            const data: StreamingData = JSON.parse(buffer.slice(6))
            onProgress(data)
            
            if (data.type === 'complete' && data.plan) {
              finalPlan = {
                success: true,
                message: data.message || '旅行计划生成成功',
                data: data.plan,
                requires_login: data.requires_login ?? false
              }
            }
          } catch (error) {
            console.error('解析最后SSE数据失败:', error)
          }
        }
        
        if (finalPlan) {
          resolve(finalPlan)
        } else {
          reject(new Error('未收到完整的旅行计划'))
        }
      } catch (error: any) {
        if (error.name === 'AbortError') {
          reject(new Error('请求已取消'))
        } else {
          reject(error)
        }
      }
    })
    .catch((error: any) => {
      if (error.name === 'AbortError') {
        reject(new Error('请求已取消'))
      } else {
        console.error('SSE连接错误:', error)
        reject(new Error('连接中断，请重试'))
      }
    })
  })
}

/**
 * 取消当前请求
 */
export function cancelCurrentRequest() {
  if (currentRequestController) {
    currentRequestController.abort()
    currentRequestController = null
  }
}

/**
 * 保存旅行计划到历史记录
 */
export async function saveTripPlan(
  request: TripFormData,
  plan: TripPlan
): Promise<{ success: boolean; message: string; data?: any }> {
  try {
    const response = await apiClient.post(
      '/api/history/trips/save',
      {
        request,
        plan
      }
    )
    return response.data
  } catch (error: any) {
    console.error('保存旅行计划失败:', error)
    throw new Error(error.response?.data?.detail || error.message || '保存计划失败')
  }
}

/**
 * 健康检查
 */
export async function healthCheck(): Promise<any> {
  try {
    const response = await apiClient.get('/health')
    return response.data
  } catch (error: any) {
    console.error('健康检查失败:', error)
    throw new Error(error.message || '健康检查失败')
  }
}

export default apiClient

