<template>
  <div class="agent-status">
    <div class="agent-item" :class="{ active: isActive, completed: isCompleted, failed: isFailed }">
      <div class="agent-icon">
        <span class="icon">{{ icon }}</span>
        <div v-if="isRunning" class="spinner"></div>
        <div v-else-if="isCompleted" class="checkmark">✓</div>
        <div v-else-if="isFailed" class="error-mark">✗</div>
      </div>
      <div class="agent-info">
        <div class="agent-name">{{ name }}</div>
        <div class="agent-message">{{ message }}</div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: `${progress}%` }"></div>
        </div>
        <div class="progress-text">{{ progress }}%</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  agent: 'attractions' | 'weather' | 'hotels' | 'planning'
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  message: string
}

const props = defineProps<Props>()

const icons = {
  attractions: '🔍',
  weather: '🌤️',
  hotels: '🏨',
  planning: '📋'
}

const names = {
  attractions: '景点搜索智能体',
  weather: '天气查询智能体',
  hotels: '酒店推荐智能体',
  planning: '行程规划智能体'
}

const icon = computed(() => icons[props.agent])
const name = computed(() => names[props.agent])
const isActive = computed(() => props.status === 'running')
const isCompleted = computed(() => props.status === 'completed')
const isFailed = computed(() => props.status === 'failed')
const isRunning = computed(() => props.status === 'running')
</script>

<style scoped>
.agent-status {
  margin-bottom: 16px;
}

.agent-item {
  display: flex;
  align-items: center;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 12px;
  border: 2px solid transparent;
  transition: all 0.3s ease;
}

.agent-item.active {
  background: linear-gradient(135deg, #e3f2fd 0%, #f5f7fa 100%);
  border-color: #2196f3;
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.2);
}

.agent-item.completed {
  background: linear-gradient(135deg, #e8f5e9 0%, #f5f7fa 100%);
  border-color: #4caf50;
}

.agent-item.failed {
  background: linear-gradient(135deg, #ffebee 0%, #f5f7fa 100%);
  border-color: #f44336;
}

.agent-icon {
  position: relative;
  width: 48px;
  height: 48px;
  margin-right: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.spinner {
  position: absolute;
  width: 48px;
  height: 48px;
  border: 3px solid #e3f2fd;
  border-top-color: #2196f3;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.checkmark {
  position: absolute;
  width: 24px;
  height: 24px;
  background: #4caf50;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: bold;
  animation: scaleIn 0.3s ease;
}

.error-mark {
  position: absolute;
  width: 24px;
  height: 24px;
  background: #f44336;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: bold;
  animation: scaleIn 0.3s ease;
}

@keyframes scaleIn {
  from {
    transform: scale(0);
  }
  to {
    transform: scale(1);
  }
}

.agent-info {
  flex: 1;
}

.agent-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.agent-message {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.progress-bar {
  width: 100%;
  height: 6px;
  background: #e0e0e0;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 4px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #2196f3 0%, #21cbf3 100%);
  border-radius: 3px;
  transition: width 0.3s ease;
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% {
    background-position: -100% 0;
  }
  100% {
    background-position: 100% 0;
  }
}

.progress-text {
  font-size: 12px;
  color: #999;
  text-align: right;
}
</style>
