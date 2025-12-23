import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserInfo } from '@/types'
import * as authService from '@/services/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserInfo | null>(authService.getStoredUser())
  const token = ref<string | null>(authService.getToken())

  const isAuthenticated = computed(() => {
    // 只要有 token 就认为已登录（user 可能还在加载中）
    // 但为了更准确，我们检查 token 是否存在
    return !!token.value
  })

  async function login(username: string, password: string) {
    try {
      // 调用登录服务
      await authService.login({ username, password })
      
      // 登录成功后，立即获取最新的 token 和 user
      const newToken = authService.getToken()
      const newUser = authService.getStoredUser()
      
      // 确保状态更新
      if (newToken) {
        token.value = newToken
      }
      
      if (newUser) {
        user.value = newUser
      } else if (newToken) {
        // 如果有 token 但没有 user，尝试获取用户信息
        const userInfo = await authService.getCurrentUser()
        if (userInfo) {
          user.value = userInfo
        }
      }
      
      // 验证登录状态
      if (!token.value) {
        throw new Error('登录失败：未获取到 token')
      }
      
      return { success: true }
    } catch (error: any) {
      // 登录失败时清除状态
      token.value = null
      user.value = null
      authService.logout() // 清除 localStorage
      return {
        success: false,
        message: error.response?.data?.detail || error.message || '登录失败'
      }
    }
  }

  async function register(username: string, email: string, password: string) {
    try {
      await authService.register({ username, email, password })
      return { success: true, message: '注册成功，请登录' }
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.detail || error.message || '注册失败'
      }
    }
  }

  function logout() {
    authService.logout()
    user.value = null
    token.value = null
  }

  async function refreshUser() {
    const userInfo = await authService.getCurrentUser()
    if (userInfo) {
      user.value = userInfo
      return true
    } else {
      logout()
      return false
    }
  }

  return {
    user,
    token,
    isAuthenticated,
    login,
    register,
    logout,
    refreshUser
  }
})

