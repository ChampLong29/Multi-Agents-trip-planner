<template>
  <div class="history-container">
    <!-- 返回按钮 -->
    <div style="margin-bottom: 16px">
      <a-button @click="goBack" type="default">
        ← 返回
      </a-button>
    </div>
    
    <a-card>
      <template #title>
        <h2>我的旅行历史</h2>
      </template>
      
      <a-tabs v-model:activeKey="activeTab">
        <a-tab-pane key="trips" tab="旅行记录">
          <a-list
            :data-source="trips"
            :loading="loading"
            :pagination="pagination"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta>
                  <template #title>
                    <a @click="viewTrip(item)">{{ item.city }}</a>
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
                  <a-space>
                    <a @click="viewTrip(item)">查看详情</a>
                    <a-popconfirm
                      title="确定要删除这条旅行记录吗？"
                      ok-text="确定"
                      cancel-text="取消"
                      @confirm="deleteTrip(item.id)"
                    >
                      <a style="color: #ff4d4f">删除</a>
                    </a-popconfirm>
                  </a-space>
                </template>
              </a-list-item>
            </template>
          </a-list>
        </a-tab-pane>
        
        <a-tab-pane key="conversations" tab="对话历史">
          <a-list
            :data-source="conversations"
            :loading="loading"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta>
                  <template #title>
                    <span :style="{ color: item.role === 'user' ? '#1890ff' : '#52c41a' }">
                      {{ item.role === 'user' ? '我' : '助手' }}
                    </span>
                  </template>
                  <template #description>
                    <div>{{ item.content }}</div>
                    <div style="color: #999; font-size: 12px; margin-top: 4px">
                      {{ formatDate(item.created_at) }}
                    </div>
                  </template>
                </a-list-item-meta>
              </a-list-item>
            </template>
          </a-list>
        </a-tab-pane>
      </a-tabs>
    </a-card>
    
    <!-- 旅行详情模态框 -->
    <a-modal
      v-model:open="tripModalVisible"
      title="旅行计划详情"
      width="800px"
      :footer="null"
    >
      <div v-if="selectedTrip">
        <a-descriptions :column="2" bordered>
          <a-descriptions-item label="目的地">{{ selectedTrip.city }}</a-descriptions-item>
          <a-descriptions-item label="日期">{{ selectedTrip.start_date }} 至 {{ selectedTrip.end_date }}</a-descriptions-item>
        </a-descriptions>
        
        <div style="margin-top: 24px">
          <a-button type="primary" @click="loadTripPlan(selectedTrip)">
            加载此计划
          </a-button>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import axios from 'axios'
import { useTripStore } from '@/stores/tripStore'

const router = useRouter()
const tripStore = useTripStore()

const activeTab = ref('trips')
const loading = ref(false)
const trips = ref<any[]>([])
const conversations = ref<any[]>([])
const tripModalVisible = ref(false)
const selectedTrip = ref<any>(null)

// 返回上一页
function goBack() {
  // 获取来源页面（从路由查询参数或 referrer）
  const referrer = document.referrer
  const from = router.currentRoute.value.query.from as string
  
  // 如果指定了来源页面，返回该页面
  if (from && (from === '/' || from === '/result')) {
    router.push(from)
    return
  }
  
  // 如果 referrer 包含我们的域名，尝试返回上一页
  if (referrer && (referrer.includes(window.location.host))) {
    router.go(-1)
    return
  }
  
  // 默认返回主页
  router.push('/')
}

const pagination = {
  pageSize: 10,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条记录`
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function formatDate(dateStr: string) {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

async function loadTrips() {
  loading.value = true
  try {
    const token = localStorage.getItem('trip_planner_token')
    const response = await axios.get(`${API_BASE_URL}/api/history/trips`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
    
    if (response.data.success) {
      trips.value = response.data.data || []
    }
  } catch (error: any) {
    message.error('加载旅行历史失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

async function loadConversations() {
  loading.value = true
  try {
    const token = localStorage.getItem('trip_planner_token')
    const response = await axios.get(`${API_BASE_URL}/api/history/conversations`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
    
    if (response.data.success) {
      conversations.value = response.data.data || []
    }
  } catch (error: any) {
    message.error('加载对话历史失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

function viewTrip(trip: any) {
  selectedTrip.value = trip
  tripModalVisible.value = true
}

function loadTripPlan(trip: any) {
  if (!trip.plan_data) {
    message.error('该历史记录没有计划数据')
    return
  }
  
  // 确保 plan_data 是对象格式
  let planData = trip.plan_data
  if (typeof planData === 'string') {
    try {
      planData = JSON.parse(planData)
    } catch (e) {
      console.error('解析计划数据失败:', e)
      message.error('计划数据格式错误，无法加载')
      return
    }
  }
  
  // 验证数据完整性
  if (!planData.days || !Array.isArray(planData.days) || planData.days.length === 0) {
    console.error('计划数据不完整:', planData)
    message.error('该历史记录的计划数据不完整（缺少days字段），无法加载')
    return
  }
  
  if (!planData.city || !planData.start_date || !planData.end_date) {
    message.error('该历史记录的计划数据缺少必要信息，无法加载')
    return
  }
  
  // 确保 days 数组中的每个 day 都有 day_index
  if (planData.days && Array.isArray(planData.days)) {
    planData.days = planData.days.map((day: any, index: number) => {
      if (day.day_index === undefined || day.day_index === null) {
        day.day_index = index
      }
      return day
    })
  }
  
  tripStore.setTripPlan(planData)
  sessionStorage.setItem('tripPlan', JSON.stringify(planData))
  message.success('计划已加载')
  tripModalVisible.value = false
  router.push('/result')
}

async function deleteTrip(tripId: number) {
  try {
    const token = localStorage.getItem('trip_planner_token')
    const response = await axios.delete(`${API_BASE_URL}/api/history/trips/${tripId}`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
    
    if (response.data.success) {
      message.success('旅行记录已删除')
      // 重新加载列表
      await loadTrips()
    }
  } catch (error: any) {
    message.error(error.response?.data?.detail || '删除失败，请稍后重试')
    console.error(error)
  }
}

onMounted(() => {
  loadTrips()
  loadConversations()
})
</script>

<style scoped>
.history-container {
  max-width: 1200px;
  margin: 0 auto;
}
</style>

