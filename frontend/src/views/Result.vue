<template>
  <div class="result-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <a-button class="back-button" size="large" @click="goBack">
        ← 返回首页
      </a-button>
      <a-space size="middle">
        <!-- 保存计划按钮 -->
        <a-button 
          v-if="!editMode && !authStore.isAuthenticated" 
          @click="handleSavePlan" 
          type="primary"
        >
          💾 登录保存此计划
        </a-button>
        <a-button 
          v-if="!editMode && authStore.isAuthenticated && !isPlanSaved" 
          @click="handleSavePlan" 
          type="primary"
        >
          💾 保存到我的历史
        </a-button>
        <a-button 
          v-if="!editMode && authStore.isAuthenticated && isPlanSaved" 
          type="default"
          disabled
        >
          ✅ 已保存
        </a-button>
        
        <a-button v-if="!editMode" @click="toggleEditMode" type="default">
          ✏️ 编辑行程
        </a-button>
        <a-button v-else @click="saveChanges" type="primary">
          💾 保存修改
        </a-button>
        <a-button v-if="editMode" @click="cancelEdit" type="default">
          ❌ 取消编辑
        </a-button>

        <!-- 导出按钮 -->
        <a-dropdown v-if="!editMode">
          <template #overlay>
            <a-menu>
              <a-menu-item key="image" @click="exportAsImage">
                📷 导出为图片
              </a-menu-item>
              <a-menu-item key="pdf" @click="exportAsPDF">
                📄 导出为PDF
              </a-menu-item>
            </a-menu>
          </template>
          <a-button type="default">
            📥 导出行程 <DownOutlined />
          </a-button>
        </a-dropdown>
      </a-space>
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoading || tripStore.isRequesting" class="loading-wrapper">
      <a-spin size="large" tip="正在加载旅行计划...">
        <div class="loading-content">
          <div v-if="tripStore.isRequesting" class="loading-progress">
            <h3 style="margin-bottom: 24px; color: #333;">智能体工作状态</h3>
            <div v-for="(progress, key) in tripStore.progress" :key="key" class="agent-progress-item">
              <div class="agent-progress-header">
                <span class="agent-icon">{{ getAgentIcon(progress.agent) }}</span>
                <span class="agent-name">{{ getAgentName(progress.agent) }}</span>
                <span class="agent-status" :class="progress.status">{{ getStatusText(progress.status) }}</span>
              </div>
              <a-progress
                :percent="progress.progress"
                :status="progress.status === 'failed' ? 'exception' : progress.status === 'completed' ? 'success' : 'active'"
                :stroke-color="getProgressColor(progress.status)"
                style="margin-top: 8px;"
              />
              <p class="agent-message">{{ progress.message }}</p>
            </div>
            <div class="overall-progress-section" style="margin-top: 24px; padding-top: 24px; border-top: 2px solid #e8e8e8;">
              <a-progress
                :percent="tripStore.overallProgress"
                status="active"
                :stroke-color="{
                  '0%': '#667eea',
                  '100%': '#764ba2',
                }"
                :stroke-width="10"
              />
              <p style="margin-top: 12px; text-align: center; color: #667eea; font-size: 16px; font-weight: 600;">
                总体进度: {{ tripStore.overallProgress }}%
              </p>
            </div>
          </div>
        </div>
      </a-spin>
    </div>

    <div v-else-if="tripPlan" class="content-wrapper">
      <!-- 侧边导航 -->
      <div class="side-nav">
        <a-affix :offset-top="80">
          <a-menu mode="inline" :selected-keys="[activeSection]" @click="scrollToSection">
            <a-menu-item key="overview">
              <span>📋 行程概览</span>
            </a-menu-item>
            <a-menu-item key="budget" v-if="tripPlan.budget">
              <span>💰 预算明细</span>
            </a-menu-item>
            <a-menu-item key="map">
              <span>📍 景点地图</span>
            </a-menu-item>
            <a-sub-menu key="days" title="📅 每日行程">
              <a-menu-item v-for="(day, index) in tripPlan.days" :key="`day-${index}`">
                第{{ day.day_index + 1 }}天
              </a-menu-item>
            </a-sub-menu>
            <a-menu-item key="weather" v-if="tripPlan.weather_info && tripPlan.weather_info.length > 0">
              <span>🌤️ 天气信息</span>
            </a-menu-item>
          </a-menu>
        </a-affix>
      </div>

      <!-- 主内容区 -->
      <div class="main-content">
        <!-- 顶部信息区:左侧概览+预算,右侧地图 -->
        <div class="top-info-section">
          <!-- 左侧:行程概览和预算明细 -->
          <div class="left-info">
            <!-- 行程概览 -->
            <a-card id="overview" :title="`${tripPlan.city}旅行计划`" :bordered="false" class="overview-card">
              <div class="overview-content">
                <div class="info-item">
                  <span class="info-label">📅 日期:</span>
                  <span class="info-value">{{ tripPlan.start_date }} 至 {{ tripPlan.end_date }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">💡 建议:</span>
                  <span class="info-value suggestions-text">{{ formatSuggestions(tripPlan.overall_suggestions) }}</span>
                </div>
              </div>
            </a-card>

            <!-- 预算明细 -->
            <a-card id="budget" v-if="tripPlan.budget" title="💰 预算明细" :bordered="false" class="budget-card">
              <div class="budget-grid">
                <div class="budget-item">
                  <div class="budget-label">景点门票</div>
                  <div class="budget-value">¥{{ tripPlan.budget.total_attractions }}</div>
                </div>
                <div class="budget-item">
                  <div class="budget-label">酒店住宿</div>
                  <div class="budget-value">¥{{ tripPlan.budget.total_hotels }}</div>
                </div>
                <div class="budget-item">
                  <div class="budget-label">餐饮费用</div>
                  <div class="budget-value">¥{{ tripPlan.budget.total_meals }}</div>
                </div>
                <div class="budget-item">
                  <div class="budget-label">交通费用</div>
                  <div class="budget-value">¥{{ tripPlan.budget.total_transportation }}</div>
                </div>
              </div>
              <div class="budget-total">
                <span class="total-label">预估总费用</span>
                <span class="total-value">¥{{ tripPlan.budget.total }}</span>
              </div>
            </a-card>
          </div>

          <!-- 右侧:地图 -->
          <div class="right-map">
            <a-card id="map" title="📍 景点地图" :bordered="false" class="map-card">
              <div id="amap-container" style="width: 100%; height: 100%"></div>
            </a-card>
          </div>
        </div>

        <!-- 每日行程:可折叠 -->
        <a-card title="📅 每日行程" :bordered="false" class="days-card">
          <a-collapse v-model:activeKey="activeDays" accordion>
            <a-collapse-panel
              v-for="(day, index) in tripPlan.days"
              :key="String(index)"
              :id="`day-${index}`"
            >
              <template #header>
                <div class="day-header">
                  <span class="day-title">第{{ day.day_index + 1 }}天</span>
                  <span class="day-date">{{ day.date }}</span>
                </div>
              </template>

              <!-- 行程基本信息 -->
              <div class="day-info">
                <div class="info-row">
                  <span class="label">📝 行程描述:</span>
                  <span class="value">{{ day.description }}</span>
                </div>
                <div class="info-row">
                  <span class="label">🚗 交通方式:</span>
                  <span class="value">{{ day.transportation }}</span>
                </div>
                <div class="info-row">
                  <span class="label">🏨 住宿:</span>
                  <span class="value">{{ day.accommodation }}</span>
                </div>
              </div>

              <!-- 景点安排 -->
              <a-divider orientation="left">🎯 景点安排</a-divider>
              <a-list
                :data-source="day.attractions"
                :grid="{ gutter: 16, column: 2 }"
              >
                <template #renderItem="{ item, index: attrIndex }">
                  <a-list-item>
                    <a-card :title="item.name" size="small" class="attraction-card">
                      <!-- 编辑模式下的操作按钮 -->
                      <template #extra v-if="editMode">
                        <a-space>
                          <a-button
                            size="small"
                            @click="moveAttraction(index, attrIndex, 'up')"
                            :disabled="attrIndex === 0"
                          >
                            ↑
                          </a-button>
                          <a-button
                            size="small"
                            @click="moveAttraction(index, attrIndex, 'down')"
                            :disabled="attrIndex === day.attractions.length - 1"
                          >
                            ↓
                          </a-button>
                          <a-button
                            size="small"
                            danger
                            @click="deleteAttraction(index, attrIndex)"
                          >
                            🗑️
                          </a-button>
                        </a-space>
                      </template>

                      <!-- 景点图片 -->
                      <div class="attraction-image-wrapper">
                        <img
                          :src="getAttractionImage(item.name, index)"
                          :alt="item.name"
                          class="attraction-image"
                          @error="handleImageError"
                        />
                        <div class="attraction-badge">
                          <span class="badge-number">{{ index + 1 }}</span>
                        </div>
                        <div v-if="item.ticket_price" class="price-tag">
                          ¥{{ item.ticket_price }}
                        </div>
                      </div>

                      <!-- 编辑模式下可编辑的字段 -->
                      <div v-if="editMode">
                        <p><strong>地址:</strong></p>
                        <a-input v-model:value="item.address" size="small" style="margin-bottom: 8px" />

                        <p><strong>游览时长(分钟):</strong></p>
                        <a-input-number v-model:value="item.visit_duration" :min="10" :max="480" size="small" style="width: 100%; margin-bottom: 8px" />

                        <p><strong>描述:</strong></p>
                        <a-textarea v-model:value="item.description" :rows="2" size="small" style="margin-bottom: 8px" />
                      </div>

                      <!-- 查看模式 -->
                      <div v-else>
                        <p><strong>地址:</strong> {{ item.address }}</p>
                        <p><strong>游览时长:</strong> {{ item.visit_duration }}分钟</p>
                        <p><strong>描述:</strong> {{ item.description }}</p>
                        <p v-if="item.rating"><strong>评分:</strong> {{ item.rating }}⭐</p>
                      </div>
                    </a-card>
                  </a-list-item>
                </template>
              </a-list>

              <!-- 酒店推荐 -->
              <a-divider v-if="day.hotel" orientation="left">🏨 住宿推荐</a-divider>
              <a-card v-if="day.hotel" size="small" class="hotel-card">
                <template #title>
                  <span class="hotel-title">{{ day.hotel.name }}</span>
                </template>
                <a-descriptions :column="2" size="small">
                  <a-descriptions-item label="地址">{{ day.hotel.address }}</a-descriptions-item>
                  <a-descriptions-item label="类型">{{ day.hotel.type }}</a-descriptions-item>
                  <a-descriptions-item label="价格范围">{{ day.hotel.price_range }}</a-descriptions-item>
                  <a-descriptions-item label="评分">{{ day.hotel.rating }}⭐</a-descriptions-item>
                  <a-descriptions-item label="距离" :span="2">{{ day.hotel.distance }}</a-descriptions-item>
                </a-descriptions>
              </a-card>

              <!-- 餐饮安排 -->
              <a-divider orientation="left">🍽️ 餐饮安排</a-divider>
              <a-descriptions :column="1" bordered size="small">
                <a-descriptions-item
                  v-for="meal in day.meals"
                  :key="meal.type"
                  :label="getMealLabel(meal.type)"
                >
                  {{ meal.name }}
                  <span v-if="meal.description"> - {{ meal.description }}</span>
                </a-descriptions-item>
              </a-descriptions>
            </a-collapse-panel>
          </a-collapse>
        </a-card>

        <a-card id="weather" v-if="tripPlan.weather_info && tripPlan.weather_info.length > 0" title="🌤️ 天气信息" style="margin-top: 20px" :bordered="false">
        <a-list
          :data-source="tripPlan.weather_info"
          :grid="{ gutter: 16, column: 2 }"
        >
          <template #renderItem="{ item }">
            <a-list-item>
              <a-card size="small" class="weather-card">
                <div class="weather-date">{{ item.date }}</div>
                <div class="weather-info-row">
                  <span class="weather-icon">☀️</span>
                  <div>
                    <div class="weather-label">白天</div>
                    <div class="weather-value">{{ item.day_weather }} {{ item.day_temp }}°C</div>
                  </div>
                </div>
                <div class="weather-info-row">
                  <span class="weather-icon">🌙</span>
                  <div>
                    <div class="weather-label">夜间</div>
                    <div class="weather-value">{{ item.night_weather }} {{ item.night_temp }}°C</div>
                  </div>
                </div>
                <div class="weather-wind">
                  💨 {{ item.wind_direction }} {{ item.wind_power }}
                </div>
                <a-divider style="margin: 12px 0;" />
                <div v-if="item.clothing_suggestion" class="weather-suggestion">
                  <div class="suggestion-label">👔 穿着建议:</div>
                  <div class="suggestion-content">{{ item.clothing_suggestion }}</div>
                </div>
                <div v-if="item.activity_suggestion" class="weather-suggestion" style="margin-top: 12px;">
                  <div class="suggestion-label">🎯 活动建议:</div>
                  <div class="suggestion-content">{{ item.activity_suggestion }}</div>
                </div>
              </a-card>
            </a-list-item>
          </template>
        </a-list>
        </a-card>
      </div>
    </div>

    <a-empty v-else description="没有找到旅行计划数据">
      <template #image>
        <div style="font-size: 80px;">🗺️</div>
      </template>
      <template #description>
        <span style="color: #999;">暂无旅行计划数据,请先创建行程</span>
      </template>
      <a-button type="primary" @click="goBack">返回首页创建行程</a-button>
    </a-empty>

    <!-- 回到顶部按钮 -->
    <a-back-top :visibility-height="300">
      <div class="back-top-button">
        ↑
      </div>
    </a-back-top>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { DownOutlined } from '@ant-design/icons-vue'
import AMapLoader from '@amap/amap-jsapi-loader'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'
import { useTripStore } from '@/stores/tripStore'
import { useAuthStore } from '@/stores/authStore'
import type { TripPlan, TripFormData } from '@/types'
import { generateTripPlan } from '@/services/api'

const router = useRouter()
const tripStore = useTripStore()
const authStore = useAuthStore()
const tripPlan = ref<TripPlan | null>(null)
const editMode = ref(false)
const originalPlan = ref<TripPlan | null>(null)
const attractionPhotos = ref<Record<string, string>>({})
const activeSection = ref('overview')
// 默认展开第一天（索引0），accordion模式下应该是字符串或数字
const activeDays = ref<string | number>(0) // 默认展开第一天
const isLoading = ref(false)
const isPlanSaved = ref(false)
let map: any = null

// 验证和修复计划数据（宽松模式，允许部分数据用于显示）
const validateAndFixPlan = (plan: any, strict: boolean = false): TripPlan | null => {
  if (!plan) {
    console.warn('validateAndFixPlan: plan 为 null 或 undefined')
    return null
  }
  
  // 创建副本，避免修改原对象导致watch无限循环
  const planCopy = JSON.parse(JSON.stringify(plan))
  
  // 确保 days 字段始终存在
  if (!planCopy.days) {
    console.warn('validateAndFixPlan: plan.days 不存在，创建空数组')
    planCopy.days = []
  } else if (!Array.isArray(planCopy.days)) {
    console.error('validateAndFixPlan: plan.days 不是数组，转换为数组')
    planCopy.days = []
  }
  
  // 修复 days 数组中的 day_index
  if (Array.isArray(planCopy.days) && planCopy.days.length > 0) {
    planCopy.days = planCopy.days.map((day: any, index: number) => {
      if (!day) {
        console.warn(`validateAndFixPlan: days[${index}] 为空，创建默认对象`)
        return {
          day_index: index,
          date: '',
          attractions: [],
          meals: [],
          transportation: '',
          accommodation: '',
          description: ''
        }
      }
      if (day.day_index === undefined || day.day_index === null) {
        day.day_index = index
      }
      // 确保每个 day 都有必要的字段
      if (!day.attractions) {
        day.attractions = []
      }
      if (!day.meals) {
        day.meals = []
      }
      return day
    })
  }
  
  // 严格模式：保存前必须验证完整性
  if (strict) {
    // 确保 days 字段存在且是数组
    if (!planCopy.days) {
      console.error('严格验证失败: 计划缺少 days 字段')
      console.error('完整计划对象:', JSON.stringify(planCopy, null, 2))
      return null
    }
    
    if (!Array.isArray(planCopy.days)) {
      console.error('严格验证失败: 计划 days 不是数组', typeof planCopy.days)
      console.error('plan.days 值:', planCopy.days)
      return null
    }
    
    if (planCopy.days.length === 0) {
      console.error('严格验证失败: 计划 days 数组为空')
      return null
    }
    
    // 确保必要字段存在
    if (!planCopy.city || !planCopy.start_date || !planCopy.end_date) {
      console.error('严格验证失败: 计划缺少必要字段')
      console.error('字段详情:', { 
        city: planCopy.city, 
        start_date: planCopy.start_date, 
        end_date: planCopy.end_date,
        hasCity: !!planCopy.city,
        hasStartDate: !!planCopy.start_date,
        hasEndDate: !!planCopy.end_date
      })
      return null
    }
    
    // 验证每个 day 的基本结构
    for (let i = 0; i < planCopy.days.length; i++) {
      const day = planCopy.days[i]
      if (!day) {
        console.error(`严格验证失败: days[${i}] 为 null 或 undefined`)
        return null
      }
      if (!day.date) {
        console.warn(`警告: days[${i}] 缺少 date 字段`)
      }
    }
  }
  
  return planCopy as TripPlan
}

// 检查计划是否已保存
const checkPlanSaved = async () => {
  if (!tripPlan.value || !authStore.isAuthenticated) {
    isPlanSaved.value = false
    return
  }
  
  // 优先检查是否有标记表示这是从历史记录加载的计划
  const planSource = sessionStorage.getItem('tripPlanSource')
  if (planSource === 'history') {
    // 从历史记录加载的计划，标记为已保存
    isPlanSaved.value = true
    console.log('检测到从历史记录加载的计划，标记为已保存')
    return
  }
  
  // 如果不是从历史加载的，检查是否已经保存过
  // 通过检查 sessionStorage 中是否有保存标记
  const savedPlanId = sessionStorage.getItem('savedPlanId')
  if (savedPlanId) {
    // 检查保存的计划ID是否与当前计划匹配
    // 这里我们通过比较计划的关键信息来判断
    const savedPlanInfo = sessionStorage.getItem('savedPlanInfo')
    if (savedPlanInfo) {
      try {
        const savedInfo = JSON.parse(savedPlanInfo)
        // 比较城市、开始日期、结束日期
        if (tripPlan.value.city === savedInfo.city &&
            tripPlan.value.start_date === savedInfo.start_date &&
            tripPlan.value.end_date === savedInfo.end_date) {
          // 当前计划已保存
          isPlanSaved.value = true
          return
        }
      } catch (e) {
        // 解析失败，清除标记
        sessionStorage.removeItem('savedPlanId')
        sessionStorage.removeItem('savedPlanInfo')
      }
    }
  }
  
  // 检查 sessionStorage 中是否有待保存的计划
  const pendingPlan = sessionStorage.getItem('pendingTripPlan')
  if (pendingPlan) {
    // 比较当前计划和pendingPlan是否相同
    try {
      const pendingPlanData = JSON.parse(pendingPlan)
      // 简单比较：城市、开始日期、结束日期
      if (tripPlan.value.city === pendingPlanData.city &&
          tripPlan.value.start_date === pendingPlanData.start_date &&
          tripPlan.value.end_date === pendingPlanData.end_date) {
        // 当前计划就是待保存的计划，还未保存
        isPlanSaved.value = false
      } else {
        // 当前计划不是待保存的计划，可能是新生成的
        isPlanSaved.value = false
      }
    } catch (e) {
      isPlanSaved.value = false
    }
  } else {
    // 没有pendingPlan，可能是新生成的计划
    isPlanSaved.value = false
  }
}

// 监听 store 中的计划更新
watch(() => tripStore.tripPlan, async (newPlan) => {
  if (newPlan) {
    // 宽松模式验证，允许显示部分数据
    const validatedPlan = validateAndFixPlan(newPlan, false)
    if (validatedPlan) {
      tripPlan.value = validatedPlan
      sessionStorage.setItem('tripPlan', JSON.stringify(validatedPlan))
      isLoading.value = false
      
      // 当计划更新时，重新检查保存状态
      // 如果计划来源不是历史记录，清除历史记录标记
      const planSource = sessionStorage.getItem('tripPlanSource')
      if (planSource !== 'history') {
        // 新生成的计划，清除保存标记，重新检查
        sessionStorage.removeItem('savedPlanId')
        sessionStorage.removeItem('savedPlanInfo')
        await checkPlanSaved()
      }
      
      // 加载景点图片和初始化地图
      nextTick(() => {
        loadAttractionPhotos()
        if (map) {
          map.destroy()
        }
        initMap()
        // 平滑滚动到顶部
        window.scrollTo({ top: 0, behavior: 'smooth' })
      })
    } else {
      console.warn('store 中的计划数据格式错误，忽略更新')
    }
  }
}, { immediate: true })

// 监听流式数据更新，逐步渲染内容
watch(() => tripStore.streamingData, (newData) => {
  if (newData && Object.keys(newData).length > 0) {
    // 如果有部分数据，可以提前显示
    if (tripPlan.value && newData.attractions && newData.attractions.length > 0) {
      // 更新景点信息
      nextTick(() => {
        loadAttractionPhotos()
        if (map) {
          initMap()
        }
      })
    }
  }
}, { deep: true })

onMounted(async () => {
  // 优先从 store 获取
  if (tripStore.tripPlan) {
    // 宽松模式验证
    const validatedPlan = validateAndFixPlan(tripStore.tripPlan, false)
    if (validatedPlan) {
      tripPlan.value = validatedPlan
    } else {
      console.warn('store 中的计划数据格式错误，清除')
      tripStore.setTripPlan(null)
    }
  } else {
    // 从 sessionStorage 获取
    const data = sessionStorage.getItem('tripPlan')
    if (data) {
      try {
        const parsedPlan = JSON.parse(data)
        // 宽松模式验证
        const validatedPlan = validateAndFixPlan(parsedPlan, false)
        if (validatedPlan) {
          tripPlan.value = validatedPlan
          tripStore.setTripPlan(validatedPlan)
        } else {
          console.warn('sessionStorage 中的计划数据格式错误，清除缓存')
          sessionStorage.removeItem('tripPlan')
        }
      } catch (e) {
        console.error('解析旅行计划失败:', e)
        sessionStorage.removeItem('tripPlan')
      }
    } else {
      // 如果没有数据，但正在请求中，等待规划完成
      if (tripStore.isRequesting) {
        isLoading.value = true
        // 监听规划完成
        const stopWatcher = watch(() => tripStore.tripPlan, (newPlan) => {
          if (newPlan) {
            // 宽松模式验证
            const validatedPlan = validateAndFixPlan(newPlan, false)
            if (validatedPlan) {
              tripPlan.value = validatedPlan
              sessionStorage.setItem('tripPlan', JSON.stringify(validatedPlan))
              isLoading.value = false
              stopWatcher()
              nextTick(() => {
                loadAttractionPhotos()
                initMap()
              })
            }
          }
        }, { immediate: true })
        return
      }
      
      // 如果没有数据且不在请求中，显示加载状态
      isLoading.value = true
      // 等待一段时间后如果还没有数据，提示用户
      setTimeout(() => {
        if (!tripPlan.value) {
          isLoading.value = false
          message.warning('未找到旅行计划数据，请返回首页重新生成')
        }
      }, 3000)
      return
    }
  }
  
  // 如果正在请求中，显示加载状态并监听完成
  if (tripStore.isRequesting) {
    isLoading.value = true
    // 监听规划完成
    const stopWatcher = watch(() => tripStore.tripPlan, (newPlan) => {
      if (newPlan && !tripPlan.value) {
        // 宽松模式验证
        const validatedPlan = validateAndFixPlan(newPlan, false)
        if (validatedPlan) {
          tripPlan.value = validatedPlan
          sessionStorage.setItem('tripPlan', JSON.stringify(validatedPlan))
          isLoading.value = false
          stopWatcher()
          nextTick(() => {
            loadAttractionPhotos()
            initMap()
          })
        }
      }
    }, { immediate: true })
  }
  
  // 检查计划是否已保存（必须在自动保存逻辑之前）
  await checkPlanSaved()
  
  // 检查是否有待保存的计划（登录后自动保存）
  // 重要：只在当前计划就是pendingPlan且不是从历史加载时才自动保存
  // 并且只在首次加载时执行一次（通过检查是否已执行过自动保存）
  if (authStore.isAuthenticated && tripPlan.value) {
    // 如果是从历史记录加载的计划，不执行自动保存
    const planSource = sessionStorage.getItem('tripPlanSource')
    if (planSource === 'history') {
      // 从历史加载的计划，清除pendingPlan标记，避免误判
      sessionStorage.removeItem('pendingTripPlan')
      console.log('从历史记录加载的计划，跳过自动保存')
    } else {
      // 检查是否已经执行过自动保存（防止重复保存）
      const autoSaveExecuted = sessionStorage.getItem('autoSaveExecuted')
      if (!autoSaveExecuted) {
        // 不是从历史加载的，检查是否有待保存的计划
        const pendingPlan = sessionStorage.getItem('pendingTripPlan')
        if (pendingPlan) {
          try {
            const plan = JSON.parse(pendingPlan)
            // 比较当前计划和pendingPlan是否相同（通过城市、日期判断）
            const isSamePlan = tripPlan.value.city === plan.city &&
                              tripPlan.value.start_date === plan.start_date &&
                              tripPlan.value.end_date === plan.end_date
            
            if (isSamePlan && !isPlanSaved.value) {
              // 当前计划就是待保存的计划，且未保存，自动保存
              const validatedPlan = validateAndFixPlan(plan, true)
              if (validatedPlan) {
                console.log('检测到待保存的计划，自动保存...')
                // 标记已执行自动保存，防止重复
                sessionStorage.setItem('autoSaveExecuted', 'true')
                await handleSavePlan(validatedPlan)
              } else {
                console.warn('待保存的计划数据不完整，跳过自动保存')
                sessionStorage.removeItem('pendingTripPlan')
              }
            } else {
              // 当前计划不是待保存的计划，或已保存，清除pendingPlan标记
              console.log('当前计划不是待保存的计划或已保存，清除pendingPlan标记')
              sessionStorage.removeItem('pendingTripPlan')
            }
          } catch (e) {
            console.error('解析待保存计划失败:', e)
            sessionStorage.removeItem('pendingTripPlan')
          }
        }
      } else {
        // 已经执行过自动保存，清除标记
        console.log('已执行过自动保存，清除标记')
        sessionStorage.removeItem('autoSaveExecuted')
        sessionStorage.removeItem('pendingTripPlan')
      }
    }
  }
  
  // 加载景点图片
  await loadAttractionPhotos()
  // 等待DOM渲染完成后初始化地图
  await nextTick()
  initMap()
  
  isLoading.value = false
})

const goBack = () => {
  router.push('/')
}

// 保存状态标记，防止重复保存
const isSaving = ref(false)

// 保存计划
const handleSavePlan = async (planToSave?: TripPlan) => {
  if (!authStore.isAuthenticated) {
    // 未登录，跳转到登录页
    router.push({ path: '/login', query: { redirect: '/result' } })
    return
  }
  
  // 检查加载状态
  if (isLoading.value) {
    message.warning('计划正在加载中，请稍候...')
    return
  }
  
  // 防止重复保存
  if (isSaving.value) {
    console.log('正在保存中，请勿重复点击')
    return
  }
  
  isSaving.value = true
  
  let plan = planToSave || tripPlan.value
  if (!plan) {
    message.error('没有可保存的计划')
    return
  }
  
  // 详细检查每个字段
  console.log('========== 保存计划调试信息 ==========')
  console.log('1. 计划对象是否存在:', !!plan)
  console.log('2. 完整的计划对象:', plan)
  console.log('3. 计划的所有键:', Object.keys(plan))
  console.log('4. days字段检查:')
  console.log('   - plan.days存在:', !!plan.days)
  console.log('   - plan.days值:', plan.days)
  console.log('   - plan.days类型:', typeof plan.days)
  console.log('   - plan.days是数组:', Array.isArray(plan.days))
  console.log('   - plan.days长度:', plan.days?.length)
  console.log('5. 其他字段检查:')
  console.log('   - city:', plan.city, '存在:', !!plan.city)
  console.log('   - start_date:', plan.start_date, '存在:', !!plan.start_date)
  console.log('   - end_date:', plan.end_date, '存在:', !!plan.end_date)
  console.log('   - weather_info:', plan.weather_info?.length, '存在:', !!plan.weather_info)
  console.log('   - overall_suggestions:', plan.overall_suggestions?.substring(0, 50), '存在:', !!plan.overall_suggestions)
  
  // 检查days数组的详细内容
  if (plan.days && Array.isArray(plan.days)) {
    console.log('6. days数组详细检查:')
    plan.days.forEach((day: any, index: number) => {
      console.log(`   Day ${index}:`, {
        day_index: day?.day_index,
        date: day?.date,
        attractions: day?.attractions?.length,
        meals: day?.meals?.length,
        transportation: day?.transportation,
        accommodation: day?.accommodation
      })
    })
  }
  console.log('====================================')
  
  // 修复缺失的days字段
  if (!plan.days || !Array.isArray(plan.days)) {
    console.error('!!!!! 发现问题：plan.days不存在或不是数组 !!!!!')
    console.error('尝试从 tripPlan.value 获取数据...')
    
    // 尝试从当前显示的 tripPlan 获取
    if (tripPlan.value && tripPlan.value.days && Array.isArray(tripPlan.value.days)) {
      console.log('从 tripPlan.value 恢复 days 数据')
      plan = { ...tripPlan.value }
    } else {
      console.error('tripPlan.value 也没有有效的 days 数据')
      plan.days = []
    }
  }
  
  const planToSaveValidated = plan as TripPlan
  
  // 再次验证
  if (!planToSaveValidated.days || planToSaveValidated.days.length === 0) {
    console.error('!!!!! 修复失败：days数组为空 !!!!!')
    console.error('当前 tripPlan.value:', tripPlan.value)
    console.error('当前 tripStore.tripPlan:', tripStore.tripPlan)
    
    // 最后尝试从 store 获取
    if (tripStore.tripPlan && tripStore.tripPlan.days && tripStore.tripPlan.days.length > 0) {
      console.log('!!!!! 从 tripStore 恢复数据 !!!!!')
      planToSaveValidated.days = tripStore.tripPlan.days
      planToSaveValidated.city = planToSaveValidated.city || tripStore.tripPlan.city
      planToSaveValidated.start_date = planToSaveValidated.start_date || tripStore.tripPlan.start_date
      planToSaveValidated.end_date = planToSaveValidated.end_date || tripStore.tripPlan.end_date
      planToSaveValidated.weather_info = planToSaveValidated.weather_info || tripStore.tripPlan.weather_info
      planToSaveValidated.overall_suggestions = planToSaveValidated.overall_suggestions || tripStore.tripPlan.overall_suggestions
    } else {
      message.error('旅行计划没有行程数据，无法保存。请刷新页面重新生成计划。')
      return
    }
  }
  
  try {
    // 构建请求数据（从计划中提取）
    const requestData: TripFormData = {
      city: planToSaveValidated.city || '未知',
      start_date: planToSaveValidated.start_date || '',
      end_date: planToSaveValidated.end_date || '',
      travel_days: planToSaveValidated.days.length,
      transportation: planToSaveValidated.days[0]?.transportation || '公共交通',
      accommodation: planToSaveValidated.days[0]?.accommodation || '经济型酒店',
      preferences: [],
      free_text_input: ''
    }
    
    // 调用新的保存 API，直接保存现有计划
    const { saveTripPlan } = await import('@/services/api')
    const result = await saveTripPlan(requestData, planToSaveValidated)
    
    if (result.success) {
      // 清除待保存的计划和自动保存标记
      sessionStorage.removeItem('pendingTripPlan')
      sessionStorage.removeItem('autoSaveExecuted')
      // 保存计划ID和信息，用于后续判断
      if (result.data && result.data.trip_id) {
        sessionStorage.setItem('savedPlanId', String(result.data.trip_id))
        sessionStorage.setItem('savedPlanInfo', JSON.stringify({
          city: planToSaveValidated.city,
          start_date: planToSaveValidated.start_date,
          end_date: planToSaveValidated.end_date
        }))
      }
      isPlanSaved.value = true
      message.success('✅ 旅行计划已成功保存到历史记录！')
      console.log('保存成功:', result)
    } else {
      message.error('保存失败：' + (result.message || '未知错误'))
      console.error('保存失败:', result)
    }
  } catch (error: any) {
    console.error('保存计划失败:', error)
    message.error('❌ 保存计划失败：' + (error.message || '网络错误，请稍后重试'))
  } finally {
    isSaving.value = false
  }
}

// 智能体状态辅助函数
const getAgentIcon = (agent: string) => {
  const icons: Record<string, string> = {
    attractions: '🔍',
    weather: '🌤️',
    hotels: '🏨',
    planning: '📋'
  }
  return icons[agent] || '🤖'
}

const getAgentName = (agent: string) => {
  const names: Record<string, string> = {
    attractions: '景点搜索智能体',
    weather: '天气查询智能体',
    hotels: '酒店推荐智能体',
    planning: '行程规划智能体'
  }
  return names[agent] || '未知智能体'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status] || status
}

const getProgressColor = (status: string) => {
  if (status === 'completed') {
    return '#52c41a'
  } else if (status === 'failed') {
    return '#ff4d4f'
  } else if (status === 'running') {
    return {
      '0%': '#2196f3',
      '100%': '#21cbf3'
    }
  }
  return '#d9d9d9'
}

// 滚动到指定区域
const scrollToSection = ({ key }: { key: string }) => {
  activeSection.value = key
  const element = document.getElementById(key)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

// 切换编辑模式
const toggleEditMode = () => {
  editMode.value = true
  // 保存原始数据用于取消编辑
  originalPlan.value = JSON.parse(JSON.stringify(tripPlan.value))
  message.info('进入编辑模式')
}

// 保存修改
const saveChanges = () => {
  editMode.value = false
  // 更新sessionStorage
  if (tripPlan.value) {
    sessionStorage.setItem('tripPlan', JSON.stringify(tripPlan.value))
    // 同时更新 store
    tripStore.setTripPlan(tripPlan.value)
  }
  message.success('修改已保存')

  // 重新初始化地图以反映更改
  // 先销毁现有地图
  if (map) {
    try {
      map.destroy()
    } catch (e) {
      console.warn('销毁地图时出错:', e)
    }
    map = null
  }
  
  // 等待 DOM 更新和响应式数据更新
  nextTick(() => {
    // 再等待一小段时间确保地图容器已准备好
    setTimeout(() => {
      const mapContainer = document.getElementById('amap-container')
      if (mapContainer && tripPlan.value) {
        initMap()
      }
    }, 100)
  })
}

// 取消编辑
const cancelEdit = () => {
  if (originalPlan.value) {
    tripPlan.value = JSON.parse(JSON.stringify(originalPlan.value))
  }
  editMode.value = false
  message.info('已取消编辑')
}

// 删除景点
const deleteAttraction = (dayIndex: number, attrIndex: number) => {
  if (!tripPlan.value) return

  const day = tripPlan.value.days[dayIndex]
  if (day.attractions.length <= 1) {
    message.warning('每天至少需要保留一个景点')
    return
  }

  day.attractions.splice(attrIndex, 1)
  message.success('景点已删除')
}

// 移动景点顺序
const moveAttraction = (dayIndex: number, attrIndex: number, direction: 'up' | 'down') => {
  if (!tripPlan.value) return

  const day = tripPlan.value.days[dayIndex]
  const attractions = day.attractions

  if (direction === 'up' && attrIndex > 0) {
    [attractions[attrIndex], attractions[attrIndex - 1]] = [attractions[attrIndex - 1], attractions[attrIndex]]
  } else if (direction === 'down' && attrIndex < attractions.length - 1) {
    [attractions[attrIndex], attractions[attrIndex + 1]] = [attractions[attrIndex + 1], attractions[attrIndex]]
  }
}

// 格式化建议文本，将数字编号后添加换行
const formatSuggestions = (text: string): string => {
  if (!text) return ''
  // 将数字编号（如 1. 2. 3.）后添加换行
  // 匹配模式：数字 + 点 + 空格（可选）
  return text.replace(/(\d+\.)\s*/g, '\n$1 ')
}

const getMealLabel = (type: string): string => {
  const labels: Record<string, string> = {
    breakfast: '早餐',
    lunch: '午餐',
    dinner: '晚餐',
    snack: '小吃'
  }
  return labels[type] || type
}

// 加载所有景点图片
const loadAttractionPhotos = async () => {
  if (!tripPlan.value) return

  const promises: Promise<void>[] = []

  tripPlan.value.days.forEach(day => {
    day.attractions.forEach(attraction => {
      const promise = fetch(`http://localhost:8000/api/poi/photo?name=${encodeURIComponent(attraction.name)}`)
        .then(res => res.json())
        .then(data => {
          if (data.success && data.data.photo_url) {
            attractionPhotos.value[attraction.name] = data.data.photo_url
          }
        })
        .catch(err => {
          console.error(`获取${attraction.name}图片失败:`, err)
        })

      promises.push(promise)
    })
  })

  await Promise.all(promises)
}

// 获取景点图片
const getAttractionImage = (name: string, index: number): string => {
  // 如果已加载真实图片,返回真实图片
  if (attractionPhotos.value[name]) {
    return attractionPhotos.value[name]
  }

  // 返回一个纯色占位图(避免跨域问题)
  const colors = [
    { start: '#667eea', end: '#764ba2' },
    { start: '#f093fb', end: '#f5576c' },
    { start: '#4facfe', end: '#00f2fe' },
    { start: '#43e97b', end: '#38f9d7' },
    { start: '#fa709a', end: '#fee140' }
  ]
  const colorIndex = index % colors.length
  const { start, end } = colors[colorIndex]

  // 使用base64编码避免中文问题
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300">
    <defs>
      <linearGradient id="grad${index}" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style="stop-color:${start};stop-opacity:1" />
        <stop offset="100%" style="stop-color:${end};stop-opacity:1" />
      </linearGradient>
    </defs>
    <rect width="400" height="300" fill="url(#grad${index})"/>
    <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="white">${name}</text>
  </svg>`

  return `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(svg)))}`
}

// 图片加载失败时的处理
const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  // 使用灰色占位图
  img.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="300"%3E%3Crect width="400" height="300" fill="%23f0f0f0"/%3E%3Ctext x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" font-family="sans-serif" font-size="18" fill="%23999"%3E图片加载失败%3C/text%3E%3C/svg%3E'
}



// 导出为图片
const exportAsImage = async () => {
  try {
    message.loading({ content: '正在生成图片...', key: 'export', duration: 0 })

    const element = document.querySelector('.main-content') as HTMLElement
    if (!element) {
      throw new Error('未找到内容元素')
    }

    // 创建一个独立的容器
    const exportContainer = document.createElement('div')
    exportContainer.style.width = element.offsetWidth + 'px'
    exportContainer.style.backgroundColor = '#f5f7fa'
    exportContainer.style.padding = '20px'

    // 复制所有内容
    exportContainer.innerHTML = element.innerHTML

    // 处理地图截图
    const mapContainer = document.getElementById('amap-container')
    if (mapContainer && map) {
      const mapCanvas = mapContainer.querySelector('canvas')
      if (mapCanvas) {
        const mapSnapshot = mapCanvas.toDataURL('image/png')
        const exportMapContainer = exportContainer.querySelector('#amap-container')
        if (exportMapContainer) {
          exportMapContainer.innerHTML = `<img src="${mapSnapshot}" style="width:100%;height:100%;object-fit:cover;" />`
        }
      }
    }

    // 移除所有ant-card类,替换为纯div
    const cards = exportContainer.querySelectorAll('.ant-card')
    cards.forEach((card) => {
      const cardEl = card as HTMLElement
      try {
        cardEl.className = '' // 移除所有类
        cardEl.style.setProperty('background-color', '#ffffff')
        cardEl.style.setProperty('border-radius', '12px')
        cardEl.style.setProperty('box-shadow', '0 4px 12px rgba(0, 0, 0, 0.1)')
        cardEl.style.setProperty('margin-bottom', '20px')
        cardEl.style.setProperty('overflow', 'hidden')
      } catch (err) {
        console.error('设置卡片样式失败:', err)
      }
    })

    // 处理卡片头部
    const cardHeads = exportContainer.querySelectorAll('.ant-card-head')
    cardHeads.forEach((head) => {
      const headEl = head as HTMLElement
      try {
        headEl.style.setProperty('background-color', '#667eea')
        headEl.style.setProperty('color', '#ffffff')
        headEl.style.setProperty('padding', '16px 24px')
        headEl.style.setProperty('font-size', '18px')
        headEl.style.setProperty('font-weight', '600')
      } catch (err) {
        console.error('设置卡片头部样式失败:', err)
      }
    })

    // 处理卡片内容
    const cardBodies = exportContainer.querySelectorAll('.ant-card-body')
    cardBodies.forEach((body) => {
      const bodyEl = body as HTMLElement
      bodyEl.style.setProperty('background-color', '#ffffff')
      bodyEl.style.setProperty('padding', '24px')
    })

    // 处理酒店卡片头部
    const hotelCards = exportContainer.querySelectorAll('.hotel-card')
    hotelCards.forEach((card) => {
      const head = card.querySelector('.ant-card-head') as HTMLElement
      if (head) {
        head.style.setProperty('background-color', '#1976d2')
      }
      (card as HTMLElement).style.setProperty('background-color', '#e3f2fd')
    })

    // 处理天气卡片
    const weatherCards = exportContainer.querySelectorAll('.weather-card')
    weatherCards.forEach((card) => {
      (card as HTMLElement).style.setProperty('background-color', '#e0f7fa')
    })

    // 处理预算总计
    const budgetTotal = exportContainer.querySelector('.budget-total')
    if (budgetTotal) {
      const el = budgetTotal as HTMLElement
      el.style.setProperty('background-color', '#667eea')
      el.style.setProperty('color', '#ffffff')
      el.style.setProperty('padding', '20px')
      el.style.setProperty('border-radius', '12px')
      el.style.setProperty('margin-bottom', '20px')
    }

    // 处理预算项
    const budgetItems = exportContainer.querySelectorAll('.budget-item')
    budgetItems.forEach((item) => {
      const el = item as HTMLElement
      el.style.setProperty('background-color', '#f5f7fa')
      el.style.setProperty('padding', '16px')
      el.style.setProperty('border-radius', '8px')
      el.style.setProperty('margin-bottom', '12px')
    })

    // 添加到body(隐藏)
    exportContainer.style.position = 'absolute'
    exportContainer.style.left = '-9999px'
    document.body.appendChild(exportContainer)

    const canvas = await html2canvas(exportContainer, {
      backgroundColor: '#f5f7fa',
      scale: 2,
      logging: false,
      useCORS: true,
      allowTaint: true
    })

    // 移除容器
    document.body.removeChild(exportContainer)

    // 转换为图片并下载
    const link = document.createElement('a')
    link.download = `旅行计划_${tripPlan.value?.city}_${new Date().getTime()}.png`
    link.href = canvas.toDataURL('image/png')
    link.click()

    message.success({ content: '图片导出成功!', key: 'export' })
  } catch (error: any) {
    console.error('导出图片失败:', error)
    message.error({ content: `导出图片失败: ${error.message}`, key: 'export' })
  }
}

// 导出为PDF
const exportAsPDF = async () => {
  try {
    message.loading({ content: '正在生成PDF...', key: 'export', duration: 0 })

    const element = document.querySelector('.main-content') as HTMLElement
    if (!element) {
      throw new Error('未找到内容元素')
    }

    // 创建一个独立的容器
    const exportContainer = document.createElement('div')
    exportContainer.style.width = element.offsetWidth + 'px'
    exportContainer.style.backgroundColor = '#f5f7fa'
    exportContainer.style.padding = '20px'

    // 复制所有内容
    exportContainer.innerHTML = element.innerHTML

    // 处理地图截图
    const mapContainer = document.getElementById('amap-container')
    if (mapContainer && map) {
      const mapCanvas = mapContainer.querySelector('canvas')
      if (mapCanvas) {
        const mapSnapshot = mapCanvas.toDataURL('image/png')
        const exportMapContainer = exportContainer.querySelector('#amap-container')
        if (exportMapContainer) {
          exportMapContainer.innerHTML = `<img src="${mapSnapshot}" style="width:100%;height:100%;object-fit:cover;" />`
        }
      }
    }

    // 移除所有ant-card类,替换为纯div
    const cards = exportContainer.querySelectorAll('.ant-card')
    cards.forEach((card) => {
      const cardEl = card as HTMLElement
      try {
        cardEl.className = ''
        cardEl.style.setProperty('background-color', '#ffffff')
        cardEl.style.setProperty('border-radius', '12px')
        cardEl.style.setProperty('box-shadow', '0 4px 12px rgba(0, 0, 0, 0.1)')
        cardEl.style.setProperty('margin-bottom', '20px')
        cardEl.style.setProperty('overflow', 'hidden')
      } catch (err) {
        console.error('设置卡片样式失败:', err)
      }
    })

    // 处理卡片头部
    const cardHeads = exportContainer.querySelectorAll('.ant-card-head')
    cardHeads.forEach((head) => {
      const headEl = head as HTMLElement
      try {
        headEl.style.setProperty('background-color', '#667eea')
        headEl.style.setProperty('color', '#ffffff')
        headEl.style.setProperty('padding', '16px 24px')
        headEl.style.setProperty('font-size', '18px')
        headEl.style.setProperty('font-weight', '600')
      } catch (err) {
        console.error('设置卡片头部样式失败:', err)
      }
    })

    // 处理卡片内容
    const cardBodies = exportContainer.querySelectorAll('.ant-card-body')
    cardBodies.forEach((body) => {
      const bodyEl = body as HTMLElement
      bodyEl.style.setProperty('background-color', '#ffffff')
      bodyEl.style.setProperty('padding', '24px')
    })

    // 处理酒店卡片头部
    const hotelCards = exportContainer.querySelectorAll('.hotel-card')
    hotelCards.forEach((card) => {
      const head = card.querySelector('.ant-card-head') as HTMLElement
      if (head) {
        head.style.setProperty('background-color', '#1976d2')
      }
      (card as HTMLElement).style.setProperty('background-color', '#e3f2fd')
    })

    // 处理天气卡片
    const weatherCards = exportContainer.querySelectorAll('.weather-card')
    weatherCards.forEach((card) => {
      (card as HTMLElement).style.setProperty('background-color', '#e0f7fa')
    })

    // 处理预算总计
    const budgetTotal = exportContainer.querySelector('.budget-total')
    if (budgetTotal) {
      const el = budgetTotal as HTMLElement
      el.style.setProperty('background-color', '#667eea')
      el.style.setProperty('color', '#ffffff')
      el.style.setProperty('padding', '20px')
      el.style.setProperty('border-radius', '12px')
      el.style.setProperty('margin-bottom', '20px')
    }

    // 处理预算项
    const budgetItems = exportContainer.querySelectorAll('.budget-item')
    budgetItems.forEach((item) => {
      const el = item as HTMLElement
      el.style.setProperty('background-color', '#f5f7fa')
      el.style.setProperty('padding', '16px')
      el.style.setProperty('border-radius', '8px')
      el.style.setProperty('margin-bottom', '12px')
    })

    // 添加到body(隐藏)
    exportContainer.style.position = 'absolute'
    exportContainer.style.left = '-9999px'
    document.body.appendChild(exportContainer)

    const canvas = await html2canvas(exportContainer, {
      backgroundColor: '#f5f7fa',
      scale: 2,
      logging: false,
      useCORS: true,
      allowTaint: true
    })

    // 移除容器
    document.body.removeChild(exportContainer)

    const imgData = canvas.toDataURL('image/png')
    const pdf = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4'
    })

    const imgWidth = 210 // A4宽度(mm)
    const imgHeight = (canvas.height * imgWidth) / canvas.width

    // 如果内容高度超过一页,分页处理
    let heightLeft = imgHeight
    let position = 0

    pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
    heightLeft -= 297 // A4高度

    while (heightLeft > 0) {
      position = heightLeft - imgHeight
      pdf.addPage()
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
      heightLeft -= 297
    }

    pdf.save(`旅行计划_${tripPlan.value?.city}_${new Date().getTime()}.pdf`)

    message.success({ content: 'PDF导出成功!', key: 'export' })
  } catch (error: any) {
    console.error('导出PDF失败:', error)
    message.error({ content: `导出PDF失败: ${error.message}`, key: 'export' })
  }
}

// 截取地图图片
const captureMapImage = async () => {
  if (!map) return

  try {
    // 获取地图容器
    const mapContainer = document.getElementById('amap-container')
    if (!mapContainer) return

    // 使用高德地图的截图功能
    const mapCanvas = mapContainer.querySelector('canvas')
    if (mapCanvas) {
      // 创建一个img元素替换地图容器
      const img = document.createElement('img')
      img.src = mapCanvas.toDataURL('image/png')
      img.style.width = '100%'
      img.style.height = '500px'
      img.style.objectFit = 'cover'
      img.id = 'map-snapshot'

      // 隐藏原地图,显示截图
      mapContainer.style.display = 'none'
      mapContainer.parentElement?.appendChild(img)
    }
  } catch (error) {
    console.error('截取地图失败:', error)
  }
}

// 恢复地图
const restoreMap = () => {
  const mapContainer = document.getElementById('amap-container')
  const snapshot = document.getElementById('map-snapshot')

  if (mapContainer) {
    mapContainer.style.display = 'block'
  }

  if (snapshot) {
    snapshot.remove()
  }
}

// 初始化地图
const initMap = async () => {
  try {
    // 从环境变量获取高德地图 Web API Key
    // 如果没有配置，使用默认的 key（可能已过期，需要用户自行配置）
    const amapKey = import.meta.env.VITE_AMAP_WEB_KEY || '25dfaf050fe024803e96badd370e8029'
    
    if (!amapKey || amapKey === 'your_amap_web_key') {
      console.warn('高德地图 Web API Key 未配置，地图可能无法正常显示')
      message.warning('地图 API Key 未配置，请配置 VITE_AMAP_WEB_KEY 环境变量')
      // 显示占位符
      const mapContainer = document.getElementById('amap-container')
      if (mapContainer) {
        mapContainer.innerHTML = `
          <div style="display: flex; align-items: center; justify-content: center; height: 100%; background: #f5f5f5; color: #999; flex-direction: column;">
            <div style="font-size: 48px; margin-bottom: 16px;">🗺️</div>
            <div>地图加载失败</div>
            <div style="font-size: 12px; margin-top: 8px;">请配置 VITE_AMAP_WEB_KEY 环境变量</div>
          </div>
        `
      }
      return
    }

    const AMap = await AMapLoader.load({
      key: amapKey,
      version: '2.0',
      plugins: ['AMap.Marker', 'AMap.Polyline', 'AMap.InfoWindow']
    })

    // 创建地图实例
    map = new AMap.Map('amap-container', {
      zoom: 12,
      center: [116.397128, 39.916527], // 默认中心点(北京)
      viewMode: '3D'
    })

    // 添加景点标记
    addAttractionMarkers(AMap)

    message.success('地图加载成功')
  } catch (error: any) {
    console.error('地图加载失败:', error)
    const mapContainer = document.getElementById('amap-container')
    if (mapContainer) {
      mapContainer.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: center; height: 100%; background: #f5f5f5; color: #999; flex-direction: column;">
          <div style="font-size: 48px; margin-bottom: 16px;">🗺️</div>
          <div>地图加载失败</div>
          <div style="font-size: 12px; margin-top: 8px; color: #ff4d4f;">${error?.message || '请检查 API Key 配置'}</div>
        </div>
      `
    }
    message.error('地图加载失败，请检查 API Key 配置')
  }
}

// 添加景点标记
const addAttractionMarkers = (AMap: any) => {
  if (!tripPlan.value) return

  const markers: any[] = []
  const allAttractions: any[] = []

  // 收集所有景点
  tripPlan.value.days.forEach((day, dayIndex) => {
    day.attractions.forEach((attraction, attrIndex) => {
      if (attraction.location && attraction.location.longitude && attraction.location.latitude) {
        allAttractions.push({
          ...attraction,
          dayIndex,
          attrIndex
        })
      }
    })
  })

  // 创建标记
  allAttractions.forEach((attraction, index) => {
    const marker = new AMap.Marker({
      position: [attraction.location.longitude, attraction.location.latitude],
      title: attraction.name,
      label: {
        content: `<div style="background: #4CAF50; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">${index + 1}</div>`,
        offset: new AMap.Pixel(0, -30)
      }
    })

    // 创建信息窗口
    const infoWindow = new AMap.InfoWindow({
      content: `
        <div style="padding: 10px;">
          <h4 style="margin: 0 0 8px 0;">${attraction.name}</h4>
          <p style="margin: 4px 0;"><strong>地址:</strong> ${attraction.address}</p>
          <p style="margin: 4px 0;"><strong>游览时长:</strong> ${attraction.visit_duration}分钟</p>
          <p style="margin: 4px 0;"><strong>描述:</strong> ${attraction.description}</p>
          <p style="margin: 4px 0; color: #1890ff;"><strong>第${attraction.dayIndex + 1}天 景点${attraction.attrIndex + 1}</strong></p>
        </div>
      `,
      offset: new AMap.Pixel(0, -30)
    })

    // 点击标记显示信息窗口
    marker.on('click', () => {
      infoWindow.open(map, marker.getPosition())
    })

    markers.push(marker)
  })

  // 添加标记到地图
  map.add(markers)

  // 自动调整视野以包含所有标记
  if (allAttractions.length > 0) {
    map.setFitView(markers)
  }

  // 绘制路线
  drawRoutes(AMap, allAttractions)
}

// 绘制路线
const drawRoutes = (AMap: any, attractions: any[]) => {
  if (attractions.length < 2) return

  // 按天分组绘制路线
  const dayGroups: any = {}
  attractions.forEach(attr => {
    if (!dayGroups[attr.dayIndex]) {
      dayGroups[attr.dayIndex] = []
    }
    dayGroups[attr.dayIndex].push(attr)
  })

  // 为每天的景点绘制路线
  Object.values(dayGroups).forEach((dayAttractions: any) => {
    if (dayAttractions.length < 2) return

    const path = dayAttractions.map((attr: any) => [
      attr.location.longitude,
      attr.location.latitude
    ])

    const polyline = new AMap.Polyline({
      path: path,
      strokeColor: '#1890ff',
      strokeWeight: 4,
      strokeOpacity: 0.8,
      strokeStyle: 'solid',
      showDir: true // 显示方向箭头
    })

    map.add(polyline)
  })
}
</script>

<style scoped>
.result-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  background-attachment: fixed;
  padding: 40px 20px;
  position: relative;
}

.result-container::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(118, 75, 162, 0.3) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
}

.result-container > * {
  position: relative;
  z-index: 1;
}

.page-header {
  max-width: 1200px;
  margin: 0 auto 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  animation: fadeInDown 0.6s ease-out;
  padding: 20px 32px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.back-button {
  border-radius: 12px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 8px 24px;
  height: auto;
}

.back-button:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
}

/* 内容布局 */
.content-wrapper {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  gap: 24px;
}

.side-nav {
  width: 240px;
  flex-shrink: 0;
}

.side-nav :deep(.ant-menu) {
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  padding: 8px;
}

.side-nav :deep(.ant-menu-item) {
  margin: 4px 8px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.side-nav :deep(.ant-menu-item-selected) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.side-nav :deep(.ant-menu-item:hover) {
  background: rgba(102, 126, 234, 0.1);
}

.main-content {
  flex: 1;
  min-width: 0;
}

/* 景点图片样式 */
.attraction-image-wrapper {
  position: relative;
  margin-bottom: 12px;
  border-radius: 8px;
  overflow: hidden;
}

.attraction-image {
  width: 100%;
  height: 200px;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.attraction-image-wrapper:hover .attraction-image {
  transform: scale(1.05);
}

.attraction-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.badge-number {
  font-size: 18px;
}

.price-tag {
  position: absolute;
  top: 12px;
  right: 12px;
  background: rgba(255, 77, 79, 0.9);
  color: white;
  padding: 4px 12px;
  border-radius: 12px;
  font-weight: bold;
  font-size: 14px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

/* 天气卡片样式 */
.weather-card {
  background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%);
  border: none !important;
  transition: all 0.3s ease;
}

.weather-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
}

.weather-date {
  font-size: 16px;
  font-weight: bold;
  color: #00796b;
  margin-bottom: 12px;
  text-align: center;
}

.weather-info-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.weather-icon {
  font-size: 24px;
}

.weather-label {
  font-size: 12px;
  color: #666;
}

.weather-value {
  font-size: 16px;
  font-weight: 600;
  color: #00796b;
}

.weather-wind {
  margin-top: 8px;
  padding-top: 8px;
}

.weather-suggestion {
  margin-top: 8px;
}

.suggestion-label {
  font-weight: 600;
  color: #333;
  font-size: 13px;
  margin-bottom: 6px;
}

.suggestion-content {
  font-size: 12px;
  color: #666;
  line-height: 1.6;
  white-space: pre-wrap;
  border-top: 1px solid rgba(0, 121, 107, 0.2);
  text-align: center;
  color: #00796b;
  font-size: 14px;
}

/* 回到顶部按钮 */
.back-top-button {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: bold;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  cursor: pointer;
  transition: all 0.3s ease;
}

.back-top-button:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
}

/* 酒店卡片样式 */
.hotel-card {
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  border: none !important;
}

.hotel-card :deep(.ant-card-head) {
  background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
}

.hotel-title {
  color: white !important;
  font-weight: 600;
}

/* 顶部信息区布局 */
.top-info-section {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.left-info {
  flex: 0 0 400px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.right-map {
  flex: 1;
}

/* 行程概览卡片 */
.overview-card {
  height: fit-content;
}

.overview-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 14px;
  font-weight: 600;
  color: #666;
}

.info-value {
  font-size: 15px;
  color: #333;
  line-height: 1.6;
  white-space: pre-line;
}

.suggestions-text {
  white-space: pre-line;
  line-height: 1.8;
}

.info-value {
  font-size: 15px;
  color: #333;
  line-height: 1.6;
}

/* 预算卡片 */
.budget-card {
  height: fit-content;
}

.budget-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.budget-item {
  text-align: center;
  padding: 20px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
  border-radius: 12px;
  border: 1px solid rgba(102, 126, 234, 0.2);
  transition: all 0.3s ease;
}

.budget-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
  border-color: rgba(102, 126, 234, 0.4);
}

.budget-label {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.budget-value {
  font-size: 20px;
  font-weight: 700;
  color: #1890ff;
}

.budget-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  color: white;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
  animation: pulse 2s ease-in-out infinite;
}

.total-label {
  font-size: 16px;
  font-weight: 600;
}

.total-value {
  font-size: 28px;
  font-weight: 700;
}

/* 地图卡片 */
.map-card {
  height: 100%;
  min-height: 500px;
}

.map-card :deep(.ant-card-body) {
  height: calc(100% - 57px);
  padding: 0;
}

/* 每日行程卡片 */
.days-card {
  margin-top: 20px;
}

.day-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.day-title {
  font-size: 20px;
  font-weight: 700;
  color: #667eea;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.day-date {
  font-size: 14px;
  color: #999;
}

.day-info {
  margin-bottom: 24px;
  padding: 24px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
  border-radius: 16px;
  border: 1px solid rgba(102, 126, 234, 0.2);
  backdrop-filter: blur(10px);
}

.info-row {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-row .label {
  font-weight: 600;
  color: #666;
  min-width: 100px;
}

.info-row .value {
  color: #333;
  flex: 1;
}

/* 卡片样式优化 - 现代化毛玻璃效果 */
:deep(.ant-card) {
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  margin-bottom: 24px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  animation: fadeInUp 0.6s ease-out;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  overflow: hidden;
}

:deep(.ant-card:hover) {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(102, 126, 234, 0.2);
}

:deep(.ant-card-head) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white !important;
  border-radius: 20px 20px 0 0;
  font-weight: 600;
  padding: 20px 24px;
  border-bottom: none;
}

:deep(.ant-card-head-title) {
  color: white !important;
  font-size: 18px;
}

:deep(.ant-card-head-title span) {
  color: white !important;
}

/* Collapse样式 */
:deep(.ant-collapse) {
  border: none;
  background: transparent;
}

:deep(.ant-collapse-item) {
  margin-bottom: 20px;
  border: 1px solid rgba(102, 126, 234, 0.2);
  border-radius: 16px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

:deep(.ant-collapse-item:hover) {
  border-color: rgba(102, 126, 234, 0.4);
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.15);
}

:deep(.ant-collapse-header) {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  padding: 20px 24px !important;
  font-weight: 600;
  font-size: 16px;
  transition: all 0.3s ease;
}

:deep(.ant-collapse-header:hover) {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
}

:deep(.ant-collapse-content) {
  border-top: 1px solid #e8e8e8;
}

:deep(.ant-collapse-content-box) {
  padding: 20px;
}

/* 统计卡片样式 */
:deep(.ant-statistic-title) {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

:deep(.ant-statistic-content) {
  font-size: 24px;
  font-weight: 600;
  color: #1890ff;
}

/* 景点卡片样式 */
:deep(.ant-list-item) {
  transition: all 0.3s ease;
}

:deep(.ant-list-item:hover) {
  transform: scale(1.02);
}

/* 动画 */
@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 加载状态 */
.loading-wrapper {
  min-height: 60vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.loading-content {
  text-align: center;
  padding: 40px;
}

.loading-progress {
  margin-top: 24px;
  max-width: 400px;
}

.loading-progress p {
  margin-top: 16px;
  color: #667eea;
  font-size: 16px;
  font-weight: 500;
}

.agent-progress-item {
  margin-bottom: 24px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 12px;
  border: 2px solid #e8e8e8;
  transition: all 0.3s ease;
}

.agent-progress-item:hover {
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
}

.agent-progress-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.agent-icon {
  font-size: 24px;
}

.agent-name {
  flex: 1;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.agent-status {
  font-size: 14px;
  padding: 4px 12px;
  border-radius: 12px;
  font-weight: 500;
}

.agent-status.pending {
  background: #f0f0f0;
  color: #999;
}

.agent-status.running {
  background: #e3f2fd;
  color: #2196f3;
  animation: pulse 2s infinite;
}

.agent-status.completed {
  background: #e8f5e9;
  color: #4caf50;
}

.agent-status.failed {
  background: #ffebee;
  color: #f44336;
}

.agent-message {
  margin-top: 8px;
  font-size: 14px;
  color: #666;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .result-container {
    padding: 20px 10px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
  }
}
</style>

