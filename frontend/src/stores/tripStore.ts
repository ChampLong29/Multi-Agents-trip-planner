import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { TripFormData, TripPlan, TripPlanResponse } from '@/types'

export interface AgentProgress {
  agent: 'attractions' | 'weather' | 'hotels' | 'planning'
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  message: string
}

export interface StreamingData {
  type: 'start' | 'progress' | 'data' | 'complete' | 'error'
  agent?: 'attractions' | 'weather' | 'hotels' | 'planning'
  status?: 'pending' | 'running' | 'completed' | 'failed'
  progress?: number
  message?: string
  data?: any
  plan?: TripPlan
  requires_login?: boolean  // 是否需要登录以保存计划
}

export const useTripStore = defineStore('trip', () => {
  // 状态
  const isRequesting = ref(false)
  const currentRequestId = ref<string | null>(null)
  const tripPlan = ref<TripPlan | null>(null)
  const error = ref<string | null>(null)
  const formData = ref<TripFormData | null>(null)  // 保存表单数据
  
  // 进度信息
  const progress = ref<Record<string, AgentProgress>>({
    attractions: {
      agent: 'attractions',
      status: 'pending',
      progress: 0,
      message: '等待开始...'
    },
    weather: {
      agent: 'weather',
      status: 'pending',
      progress: 0,
      message: '等待开始...'
    },
    hotels: {
      agent: 'hotels',
      status: 'pending',
      progress: 0,
      message: '等待开始...'
    },
    planning: {
      agent: 'planning',
      status: 'pending',
      progress: 0,
      message: '等待开始...'
    }
  })
  
  // 流式数据
  const streamingData = ref<{
    attractions: any[]
    weather: any[]
    hotels: any[]
  }>({
    attractions: [],
    weather: [],
    hotels: []
  })
  
  // 计算属性
  const overallProgress = computed(() => {
    const progresses = Object.values(progress.value)
    const total = progresses.reduce((sum, p) => sum + p.progress, 0)
    return Math.round(total / progresses.length)
  })
  
  const isAllCompleted = computed(() => {
    return Object.values(progress.value).every(p => p.status === 'completed')
  })
  
  const hasError = computed(() => {
    return Object.values(progress.value).some(p => p.status === 'failed') || error.value !== null
  })
  
  // 方法
  function startRequest(requestId: string) {
    isRequesting.value = true
    currentRequestId.value = requestId
    error.value = null
    
    // 重置进度
    Object.keys(progress.value).forEach(key => {
      progress.value[key] = {
        agent: key as any,
        status: 'pending',
        progress: 0,
        message: '等待开始...'
      }
    })
    
    // 重置流式数据
    streamingData.value = {
      attractions: [],
      weather: [],
      hotels: []
    }
  }
  
  function updateProgress(update: StreamingData) {
    if (update.type === 'progress' && update.agent) {
      const agentKey = update.agent
      if (progress.value[agentKey]) {
        progress.value[agentKey] = {
          agent: agentKey,
          status: update.status || 'running',
          progress: update.progress || 0,
          message: update.message || '处理中...'
        }
      }
    } else if (update.type === 'data' && update.agent) {
      const agentKey = update.agent
      if (streamingData.value[agentKey]) {
        streamingData.value[agentKey] = update.data || []
      }
    } else if (update.type === 'complete' && update.plan) {
      console.log('🔍 [tripStore] 收到complete事件，plan数据:')
      console.log('  - plan对象:', update.plan)
      console.log('  - plan.days存在:', !!update.plan.days)
      console.log('  - plan.days类型:', typeof update.plan.days)
      console.log('  - plan.days是数组:', Array.isArray(update.plan.days))
      console.log('  - plan.days长度:', update.plan.days?.length)
      if (update.plan.days && Array.isArray(update.plan.days) && update.plan.days.length > 0) {
        console.log('  - 第一天数据:', update.plan.days[0])
      }
      
      tripPlan.value = update.plan
      console.log('  - 已设置tripPlan.value')
      
      // 标记所有进度为完成
      Object.keys(progress.value).forEach(key => {
        if (progress.value[key].status !== 'completed') {
          progress.value[key].status = 'completed'
          progress.value[key].progress = 100
        }
      })
    } else if (update.type === 'error') {
      error.value = update.message || '发生未知错误'
      // 标记所有进度为失败
      Object.keys(progress.value).forEach(key => {
        if (progress.value[key].status === 'running') {
          progress.value[key].status = 'failed'
        }
      })
    }
  }
  
  function finishRequest() {
    isRequesting.value = false
    currentRequestId.value = null
  }
  
  function setTripPlan(plan: TripPlan) {
    tripPlan.value = plan
  }
  
  function setError(err: string) {
    error.value = err
    isRequesting.value = false
  }
  
  function reset() {
    isRequesting.value = false
    currentRequestId.value = null
    tripPlan.value = null
    error.value = null
    formData.value = null
    Object.keys(progress.value).forEach(key => {
      progress.value[key] = {
        agent: key as any,
        status: 'pending',
        progress: 0,
        message: '等待开始...'
      }
    })
    streamingData.value = {
      attractions: [],
      weather: [],
      hotels: []
    }
  }
  
  function saveFormData(data: TripFormData) {
    formData.value = data
    // 同时保存到 sessionStorage
    sessionStorage.setItem('tripFormData', JSON.stringify(data))
  }
  
  function getFormData(): TripFormData | null {
    // 优先从 store 获取
    if (formData.value) {
      return formData.value
    }
    // 从 sessionStorage 获取
    const saved = sessionStorage.getItem('tripFormData')
    if (saved) {
      try {
        return JSON.parse(saved)
      } catch {
        return null
      }
    }
    return null
  }
  
  function clearFormData() {
    formData.value = null
    sessionStorage.removeItem('tripFormData')
  }
  
  return {
    // 状态
    isRequesting,
    currentRequestId,
    tripPlan,
    error,
    progress,
    streamingData,
    formData,
    
    // 计算属性
    overallProgress,
    isAllCompleted,
    hasError,
    
    // 方法
    startRequest,
    updateProgress,
    finishRequest,
    setTripPlan,
    setError,
    reset,
    saveFormData,
    getFormData,
    clearFormData
  }
})

