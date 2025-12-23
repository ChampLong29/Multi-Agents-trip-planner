import axios from 'axios'
import type { UserInfo } from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const TOKEN_KEY = 'trip_planner_token'
const USER_KEY = 'trip_planner_user'

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface AuthResponse {
  success: boolean
  message: string
  data?: UserInfo
}

/**
 * 登录
 */
export async function login(credentials: LoginRequest): Promise<TokenResponse> {
  const response = await axios.post<TokenResponse>(
    `${API_BASE_URL}/api/auth/login`,
    credentials
  )
  
  const token = response.data.access_token
  localStorage.setItem(TOKEN_KEY, token)
  
  // 获取用户信息（必须成功，否则登录失败）
  try {
    const userInfo = await getCurrentUser()
    if (!userInfo) {
      // 如果获取用户信息失败，清除 token
      localStorage.removeItem(TOKEN_KEY)
      throw new Error('获取用户信息失败，请检查网络连接或稍后重试')
    }
    localStorage.setItem(USER_KEY, JSON.stringify(userInfo))
  } catch (error: any) {
    // 如果获取用户信息失败，清除 token
    localStorage.removeItem(TOKEN_KEY)
    // 如果是我们抛出的错误，直接抛出；否则包装错误信息
    if (error.message && error.message.includes('获取用户信息失败')) {
      throw error
    }
    throw new Error(error.response?.data?.detail || error.message || '获取用户信息失败')
  }
  
  return response.data
}

/**
 * 注册
 */
export async function register(userData: RegisterRequest): Promise<AuthResponse> {
  const response = await axios.post<AuthResponse>(
    `${API_BASE_URL}/api/auth/register`,
    userData
  )
  
  return response.data
}

/**
 * 登出
 */
export function logout(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

/**
 * 获取当前用户信息
 */
export async function getCurrentUser(): Promise<UserInfo | null> {
  const token = getToken()
  if (!token) {
    return null
  }
  
  try {
    const response = await axios.get<AuthResponse>(
      `${API_BASE_URL}/api/auth/me`,
      {
        headers: {
          Authorization: `Bearer ${token}`
        }
      }
    )
    
    if (response.data.success && response.data.data) {
      localStorage.setItem(USER_KEY, JSON.stringify(response.data.data))
      return response.data.data
    }
    
    // 如果响应不成功，记录错误
    console.error('获取用户信息失败:', response.data)
    return null
  } catch (error: any) {
    // 记录详细错误信息
    console.error('获取用户信息异常:', error.response?.data || error.message)
    
    // 如果是401错误，说明token无效，清除token
    if (error.response?.status === 401) {
      logout()
    }
    
    return null
  }
}

/**
 * 获取存储的Token
 */
export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

/**
 * 获取存储的用户信息
 */
export function getStoredUser(): UserInfo | null {
  const userStr = localStorage.getItem(USER_KEY)
  if (userStr) {
    try {
      return JSON.parse(userStr)
    } catch {
      return null
    }
  }
  return null
}

/**
 * 检查是否已登录
 */
export function isAuthenticated(): boolean {
  return !!getToken()
}

