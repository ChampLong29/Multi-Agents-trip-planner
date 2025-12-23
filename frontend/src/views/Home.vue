<template>
  <div class="home-container">
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
    </div>

    <!-- 页面标题 -->
    <div class="page-header">
      <div class="icon-wrapper">
        <span class="icon">✈️</span>
      </div>
      <h1 class="page-title">智能旅行助手</h1>
      <p class="page-subtitle">基于AI的个性化旅行规划,让每一次出行都完美无忧</p>
    </div>

    <!-- 历史记录预览（仅登录用户显示） -->
    <a-card v-if="authStore.isAuthenticated && recentTrips.length > 0" class="history-preview-card" :bordered="false">
      <template #title>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span>📋 最近的历史记录</span>
          <a-button type="link" @click="$router.push('/history')">查看全部 →</a-button>
        </div>
      </template>
      <a-list :data-source="recentTrips" :loading="loadingHistory">
        <template #renderItem="{ item }">
          <a-list-item>
            <a-list-item-meta>
              <template #title>
                <a @click="viewHistoryTrip(item)">{{ item.city }}</a>
              </template>
              <template #description>
                <div>
                  <div>{{ item.start_date }} 至 {{ item.end_date }}</div>
                  <div style="color: #999; font-size: 12px; margin-top: 4px">
                    {{ formatDate(item.created_at) }}
                  </div>
                </div>
              </template>
            </a-list-item-meta>
            <template #actions>
              <a @click="viewHistoryTrip(item)">查看详情</a>
            </template>
          </a-list-item>
        </template>
      </a-list>
    </a-card>

    <a-card class="form-card" :bordered="false">
      <a-form
        :model="formData"
        layout="vertical"
        @finish="handleSubmit"
      >
        <!-- 第一步:目的地和日期 -->
        <div class="form-section">
          <div class="section-header">
            <span class="section-icon">📍</span>
            <span class="section-title">目的地与日期</span>
          </div>

          <a-row :gutter="24">
            <a-col :span="8">
              <a-form-item name="city" :rules="[{ required: true, message: '请输入目的地城市' }]">
                <template #label>
                  <span class="form-label">目的地城市</span>
                </template>
                <a-input
                  v-model:value="formData.city"
                  placeholder="例如: 北京"
                  size="large"
                  class="custom-input"
                >
                  <template #prefix>
                    <span style="color: #1890ff;">🏙️</span>
                  </template>
                </a-input>
              </a-form-item>
            </a-col>
            <a-col :span="6">
              <a-form-item name="start_date" :rules="[{ required: true, message: '请选择开始日期' }]">
                <template #label>
                  <span class="form-label">开始日期</span>
                </template>
                <a-date-picker
                  v-model:value="formData.start_date"
                  style="width: 100%"
                  size="large"
                  class="custom-input"
                  placeholder="选择日期"
                />
              </a-form-item>
            </a-col>
            <a-col :span="6">
              <a-form-item name="end_date" :rules="[{ required: true, message: '请选择结束日期' }]">
                <template #label>
                  <span class="form-label">结束日期</span>
                </template>
                <a-date-picker
                  v-model:value="formData.end_date"
                  style="width: 100%"
                  size="large"
                  class="custom-input"
                  placeholder="选择日期"
                />
              </a-form-item>
            </a-col>
            <a-col :span="4">
              <a-form-item>
                <template #label>
                  <span class="form-label">旅行天数</span>
                </template>
                <div class="days-display-compact">
                  <span class="days-value">{{ formData.travel_days }}</span>
                  <span class="days-unit">天</span>
                </div>
              </a-form-item>
            </a-col>
          </a-row>
        </div>

        <!-- 第二步:偏好设置 -->
        <div class="form-section">
          <div class="section-header">
            <span class="section-icon">⚙️</span>
            <span class="section-title">偏好设置</span>
          </div>

          <a-row :gutter="24">
            <a-col :span="8">
              <a-form-item name="transportation">
                <template #label>
                  <span class="form-label">交通方式</span>
                </template>
                <a-select v-model:value="formData.transportation" size="large" class="custom-select">
                  <a-select-option value="公共交通">🚇 公共交通</a-select-option>
                  <a-select-option value="自驾">🚗 自驾</a-select-option>
                  <a-select-option value="步行">🚶 步行</a-select-option>
                  <a-select-option value="混合">🔀 混合</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item name="accommodation">
                <template #label>
                  <span class="form-label">住宿偏好</span>
                </template>
                <a-select v-model:value="formData.accommodation" size="large" class="custom-select">
                  <a-select-option value="经济型酒店">💰 经济型酒店</a-select-option>
                  <a-select-option value="舒适型酒店">🏨 舒适型酒店</a-select-option>
                  <a-select-option value="豪华酒店">⭐ 豪华酒店</a-select-option>
                  <a-select-option value="民宿">🏡 民宿</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item name="preferences">
                <template #label>
                  <span class="form-label">旅行偏好</span>
                </template>
                <div class="preference-tags">
                  <a-checkbox-group v-model:value="formData.preferences" class="custom-checkbox-group">
                    <a-checkbox value="历史文化" class="preference-tag">🏛️ 历史文化</a-checkbox>
                    <a-checkbox value="自然风光" class="preference-tag">🏞️ 自然风光</a-checkbox>
                    <a-checkbox value="美食" class="preference-tag">🍜 美食</a-checkbox>
                    <a-checkbox value="购物" class="preference-tag">🛍️ 购物</a-checkbox>
                    <a-checkbox value="艺术" class="preference-tag">🎨 艺术</a-checkbox>
                    <a-checkbox value="休闲" class="preference-tag">☕ 休闲</a-checkbox>
                  </a-checkbox-group>
                </div>
              </a-form-item>
            </a-col>
          </a-row>
        </div>

        <!-- 第三步:额外要求 -->
        <div class="form-section">
          <div class="section-header">
            <span class="section-icon">💬</span>
            <span class="section-title">额外要求</span>
          </div>

          <a-form-item name="free_text_input">
            <a-textarea
              v-model:value="formData.free_text_input"
              placeholder="请输入您的额外要求,例如:想去看升旗、需要无障碍设施、对海鲜过敏等..."
              :rows="3"
              size="large"
              class="custom-textarea"
            />
          </a-form-item>
        </div>

        <!-- 提交按钮 -->
        <a-form-item>
          <a-space :size="16" style="width: 100%">
            <a-button
              type="primary"
              html-type="submit"
              :loading="tripStore.isRequesting"
              :disabled="tripStore.isRequesting"
              size="large"
              block
              class="submit-button"
            >
              <template v-if="!tripStore.isRequesting">
                <span class="button-icon">🚀</span>
                <span>开始规划我的旅行</span>
              </template>
              <template v-else>
                <span>正在生成中... ({{ tripStore.overallProgress }}%)</span>
              </template>
            </a-button>
            <a-button
              v-if="tripStore.isRequesting"
              @click="handleCancel"
              size="large"
              danger
            >
              取消
            </a-button>
          </a-space>
        </a-form-item>

        <!-- 智能体状态显示 -->
        <a-form-item v-if="tripStore.isRequesting">
          <div class="agents-status-container">
            <h3 class="status-title">智能体工作状态</h3>
            <AgentStatus
              v-for="(progress, key) in tripStore.progress"
              :key="key"
              :agent="progress.agent"
              :status="progress.status"
              :progress="progress.progress"
              :message="progress.message"
            />
            <div class="overall-progress">
              <a-progress
                :percent="tripStore.overallProgress"
                status="active"
                :stroke-color="{
                  '0%': '#667eea',
                  '100%': '#764ba2',
                }"
                :stroke-width="8"
              />
              <p class="progress-text">总体进度: {{ tripStore.overallProgress }}%</p>
            </div>
          </div>
        </a-form-item>

        <!-- 流式内容预览 -->
        <a-form-item v-if="tripStore.isRequesting && hasStreamingData">
          <StreamingContent
            :attractions="tripStore.streamingData.attractions"
            :weather="tripStore.streamingData.weather"
            :hotels="tripStore.streamingData.hotels"
          />
        </a-form-item>

        <!-- 错误提示 -->
        <a-form-item v-if="tripStore.error">
          <a-alert
            :message="tripStore.error"
            type="error"
            show-icon
            closable
            @close="tripStore.setError(null)"
          >
            <template #action>
              <a-button size="small" @click="handleRetry">重试</a-button>
            </template>
          </a-alert>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch, computed, onUnmounted, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { generateTripPlanStream, cancelCurrentRequest } from '@/services/api'
import apiClient from '@/services/api'
import { useTripStore } from '@/stores/tripStore'
import { useAuthStore } from '@/stores/authStore'
import AgentStatus from '@/components/AgentStatus.vue'
import StreamingContent from '@/components/StreamingContent.vue'
import type { TripFormData } from '@/types'
import type { Dayjs } from 'dayjs'

const router = useRouter()
const tripStore = useTripStore()
const authStore = useAuthStore()
const recentTrips = ref<any[]>([])
const loadingHistory = ref(false)

const formData = reactive<TripFormData & { start_date: Dayjs | null; end_date: Dayjs | null }>({
  city: '',
  start_date: null,
  end_date: null,
  travel_days: 1,
  transportation: '公共交通',
  accommodation: '经济型酒店',
  preferences: [],
  free_text_input: ''
})

// 计算属性
const hasStreamingData = computed(() => {
  return tripStore.streamingData.attractions.length > 0 ||
         tripStore.streamingData.weather.length > 0 ||
         tripStore.streamingData.hotels.length > 0
})

// 监听日期变化,自动计算旅行天数
watch([() => formData.start_date, () => formData.end_date], ([start, end]: [any, any]) => {
  if (start && end) {
    const days = end.diff(start, 'day') + 1
    if (days > 0 && days <= 30) {
      formData.travel_days = days
    } else if (days > 30) {
      message.warning('旅行天数不能超过30天')
      formData.end_date = null
    } else {
      message.warning('结束日期不能早于开始日期')
      formData.end_date = null
    }
  }
})

// 加载历史记录
const loadHistory = async () => {
  if (!authStore.isAuthenticated) {
    return
  }
  
  loadingHistory.value = true
  try {
    const response = await apiClient.get('/api/history/trips', {
      params: { limit: 5 }
    })
    if (response.data.success && response.data.data) {
      recentTrips.value = response.data.data
    }
  } catch (error) {
    console.error('加载历史记录失败:', error)
  } finally {
    loadingHistory.value = false
  }
}

// 格式化日期
const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

// 查看历史记录
const viewHistoryTrip = (item: any) => {
  // 跳转到结果页，并加载该计划
  router.push(`/result?trip_id=${item.id}`)
}

// 监听登录状态变化
watch(() => authStore.isAuthenticated, (isAuth) => {
  if (isAuth) {
    loadHistory()
  } else {
    recentTrips.value = []
  }
})

// 组件挂载时加载历史记录和恢复表单数据
onMounted(async () => {
  if (authStore.isAuthenticated) {
    loadHistory()
  }
  
  // 恢复保存的表单数据
  const savedFormData = tripStore.getFormData()
  if (savedFormData) {
    // 恢复基本字段
    formData.city = savedFormData.city
    formData.travel_days = savedFormData.travel_days
    formData.transportation = savedFormData.transportation
    formData.accommodation = savedFormData.accommodation
    formData.preferences = savedFormData.preferences || []
    formData.free_text_input = savedFormData.free_text_input || ''
    
    // 恢复日期（需要从字符串转换为 Dayjs 对象）
    if (savedFormData.start_date) {
      const dayjs = (await import('dayjs')).default
      formData.start_date = dayjs(savedFormData.start_date)
    }
    if (savedFormData.end_date) {
      const dayjs = (await import('dayjs')).default
      formData.end_date = dayjs(savedFormData.end_date)
    }
  }
  
  // 如果正在请求中，监听规划完成事件
  if (tripStore.isRequesting) {
    const stopWatcher = watch(() => tripStore.tripPlan, (newPlan) => {
      if (newPlan) {
        // 规划完成，跳转到结果页
        message.success('旅行计划生成成功!')
        stopWatcher() // 停止监听
        setTimeout(() => {
          router.push('/result')
        }, 500)
      }
    }, { immediate: true })
  }
  
  // 如果已经有规划结果，检查是否需要跳转
  if (tripStore.tripPlan && !tripStore.isRequesting) {
    // 已经有规划结果，可能用户从其他页面返回，不需要自动跳转
  }
})

// 不再在组件卸载时取消请求，让请求继续在后台进行
// 这样用户可以在其他页面查看，请求完成后会自动跳转到结果页

const handleSubmit = async () => {
  // 防重复提交检查
  if (tripStore.isRequesting) {
    message.warning('请求正在进行中，请勿重复提交')
    return
  }

  if (!formData.start_date || !formData.end_date) {
    message.error('请选择日期')
    return
  }

  if (!formData.city.trim()) {
    message.error('请输入目的地城市')
    return
  }

  // 生成请求ID
  const requestId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  tripStore.startRequest(requestId)

  try {
    const requestData: TripFormData = {
      city: formData.city.trim(),
      start_date: formData.start_date.format('YYYY-MM-DD'),
      end_date: formData.end_date.format('YYYY-MM-DD'),
      travel_days: formData.travel_days,
      transportation: formData.transportation,
      accommodation: formData.accommodation,
      preferences: formData.preferences,
      free_text_input: formData.free_text_input
    }
    
    // 保存表单数据到 store 和 sessionStorage
    tripStore.saveFormData(requestData)

    // 使用流式请求
    const response = await generateTripPlanStream(
      requestData,
      (update) => {
        tripStore.updateProgress(update)
      }
    )

    if (response.success && response.data) {
      // 保存到store和sessionStorage
      tripStore.setTripPlan(response.data)
      sessionStorage.setItem('tripPlan', JSON.stringify(response.data))
      
      // 如果未登录且需要登录保存，显示登录提示
      const authStore = useAuthStore()
      if (response.requires_login && !authStore.isAuthenticated) {
        // 保存计划到 sessionStorage，以便登录后保存
        sessionStorage.setItem('pendingTripPlan', JSON.stringify(response.data))
        
        message.warning('计划已生成，登录后可保存到历史记录', 5)
        
        // 显示登录提示弹窗
        Modal.confirm({
          title: '登录保存计划',
          content: '您还未登录，登录后可以保存此计划到历史记录，方便以后查看。',
          okText: '立即登录',
          cancelText: '稍后登录',
          onOk: () => {
            router.push({ path: '/login', query: { redirect: '/result' } })
          },
          onCancel: () => {
            // 用户选择稍后登录，直接跳转到结果页
            setTimeout(() => {
              router.push('/result')
            }, 500)
          }
        })
      } else {
        message.success('旅行计划生成成功!')
        // 短暂延迟后跳转
        setTimeout(() => {
          router.push('/result')
        }, 500)
      }
    } else {
      tripStore.setError(response.message || '生成失败')
      message.error(response.message || '生成失败')
    }
  } catch (error: any) {
    const errorMessage = error.message || '生成旅行计划失败,请稍后重试'
    tripStore.setError(errorMessage)
    message.error(errorMessage)
  } finally {
    tripStore.finishRequest()
  }
}

const handleRetry = () => {
  tripStore.setError(null)
  handleSubmit()
}

const handleCancel = () => {
  cancelCurrentRequest()
  tripStore.reset()
  message.info('已取消请求')
}
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 60px 20px;
  position: relative;
  overflow: hidden;
}

/* 背景装饰 */
.bg-decoration {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  overflow: hidden;
}

.circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  animation: float 20s infinite ease-in-out;
}

.circle-1 {
  width: 300px;
  height: 300px;
  top: -100px;
  left: -100px;
  animation-delay: 0s;
}

.circle-2 {
  width: 200px;
  height: 200px;
  top: 50%;
  right: -50px;
  animation-delay: 5s;
}

.circle-3 {
  width: 150px;
  height: 150px;
  bottom: -50px;
  left: 30%;
  animation-delay: 10s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-30px) rotate(180deg);
  }
}

/* 页面标题 */
.page-header {
  text-align: center;
  margin-bottom: 50px;
  animation: fadeInDown 0.8s ease-out;
  position: relative;
  z-index: 1;
}

.icon-wrapper {
  margin-bottom: 20px;
}

.icon {
  font-size: 80px;
  display: inline-block;
  animation: bounce 2s infinite;
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-20px);
  }
}

.page-title {
  font-size: 56px;
  font-weight: 800;
  color: #ffffff;
  margin-bottom: 16px;
  text-shadow: 3px 3px 6px rgba(0, 0, 0, 0.3);
  letter-spacing: 2px;
}

.page-subtitle {
  font-size: 20px;
  color: rgba(255, 255, 255, 0.95);
  margin: 0;
  font-weight: 300;
}

/* 历史记录预览卡片 */
.history-preview-card {
  max-width: 1400px;
  margin: 0 auto 30px;
  border-radius: 24px;
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.4);
  animation: fadeInUp 0.8s ease-out;
  position: relative;
  z-index: 1;
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.98) !important;
}

/* 表单卡片 */
.form-card {
  max-width: 1400px;
  margin: 0 auto;
  border-radius: 24px;
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.4);
  animation: fadeInUp 0.8s ease-out;
  position: relative;
  z-index: 1;
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.98) !important;
}

/* 表单分区 */
.form-section {
  margin-bottom: 32px;
  padding: 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
  border-radius: 16px;
  border: 1px solid #e8e8e8;
  transition: all 0.3s ease;
}

.form-section:hover {
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.15);
  transform: translateY(-2px);
}

.section-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid #667eea;
}

.section-icon {
  font-size: 24px;
  margin-right: 12px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

/* 表单标签 */
.form-label {
  font-size: 15px;
  font-weight: 500;
  color: #555;
}

/* 自定义输入框 */
.custom-input :deep(.ant-input),
.custom-input :deep(.ant-picker) {
  border-radius: 12px;
  border: 2px solid #e8e8e8;
  transition: all 0.3s ease;
}

.custom-input :deep(.ant-input:hover),
.custom-input :deep(.ant-picker:hover) {
  border-color: #667eea;
}

.custom-input :deep(.ant-input:focus),
.custom-input :deep(.ant-picker-focused) {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* 自定义选择框 */
.custom-select :deep(.ant-select-selector) {
  border-radius: 12px !important;
  border: 2px solid #e8e8e8 !important;
  transition: all 0.3s ease;
}

.custom-select:hover :deep(.ant-select-selector) {
  border-color: #667eea !important;
}

.custom-select :deep(.ant-select-focused .ant-select-selector) {
  border-color: #667eea !important;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
}

/* 天数显示 - 紧凑版 */
.days-display-compact {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 40px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
}

.days-display-compact .days-value {
  font-size: 24px;
  font-weight: 700;
  margin-right: 4px;
}

.days-display-compact .days-unit {
  font-size: 14px;
}

/* 偏好标签 */
.preference-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.custom-checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  width: 100%;
}

.preference-tag :deep(.ant-checkbox-wrapper) {
  margin: 0 !important;
  padding: 8px 16px;
  border: 2px solid #e8e8e8;
  border-radius: 20px;
  transition: all 0.3s ease;
  background: white;
  font-size: 14px;
}

.preference-tag :deep(.ant-checkbox-wrapper:hover) {
  border-color: #667eea;
  background: #f5f7ff;
}

.preference-tag :deep(.ant-checkbox-wrapper-checked) {
  border-color: #667eea;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

/* 自定义文本域 */
.custom-textarea :deep(.ant-input) {
  border-radius: 12px;
  border: 2px solid #e8e8e8;
  transition: all 0.3s ease;
}

.custom-textarea :deep(.ant-input:hover) {
  border-color: #667eea;
}

.custom-textarea :deep(.ant-input:focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* 提交按钮 */
.submit-button {
  height: 56px;
  border-radius: 28px;
  font-size: 18px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
  transition: all 0.3s ease;
}

.submit-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(102, 126, 234, 0.5);
}

.submit-button:active {
  transform: translateY(0);
}

.button-icon {
  margin-right: 8px;
  font-size: 20px;
}

/* 智能体状态容器 */
.agents-status-container {
  padding: 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
  border-radius: 16px;
  border: 2px solid #e8e8e8;
  animation: fadeInUp 0.5s ease;
}

.status-title {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin-bottom: 20px;
  text-align: center;
}

.overall-progress {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 2px solid #e8e8e8;
}

.progress-text {
  margin-top: 12px;
  text-align: center;
  color: #667eea;
  font-size: 16px;
  font-weight: 600;
}

/* 加载容器 */
.loading-container {
  text-align: center;
  padding: 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
  border-radius: 16px;
  border: 2px dashed #667eea;
}

.loading-status {
  margin-top: 16px;
  color: #667eea;
  font-size: 18px;
  font-weight: 500;
}

/* 动画 */
@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

