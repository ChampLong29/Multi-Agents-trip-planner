<template>
  <div class="streaming-content">
    <a-card v-if="attractions.length > 0" title="🔍 已找到的景点" class="content-card">
      <a-list :data-source="attractions" :grid="{ gutter: 16, column: 2 }">
        <template #renderItem="{ item }">
          <a-list-item>
            <a-card size="small" class="item-card">
              <div class="item-name">{{ item.name }}</div>
              <div class="item-address">{{ item.address }}</div>
            </a-card>
          </a-list-item>
        </template>
      </a-list>
    </a-card>

    <a-card v-if="weather.length > 0" title="🌤️ 天气信息" class="content-card">
      <a-list :data-source="weather" :grid="{ gutter: 16, column: 2 }">
        <template #renderItem="{ item }">
          <a-list-item>
            <a-card size="small" class="weather-card">
              <div class="weather-date">{{ item.date }}</div>
              <div class="weather-temp">{{ item.day_temp }}°C / {{ item.night_temp }}°C</div>
              <div class="weather-desc">{{ item.day_weather }}</div>
              <a-divider style="margin: 8px 0;" />
              <div v-if="item.clothing_suggestion" class="weather-suggestion">
                <div class="suggestion-label">👔 穿着建议:</div>
                <div class="suggestion-content">{{ item.clothing_suggestion }}</div>
              </div>
              <div v-if="item.activity_suggestion" class="weather-suggestion" style="margin-top: 8px;">
                <div class="suggestion-label">🎯 活动建议:</div>
                <div class="suggestion-content">{{ item.activity_suggestion }}</div>
              </div>
            </a-card>
          </a-list-item>
        </template>
      </a-list>
    </a-card>

    <a-card v-if="hotels.length > 0" title="🏨 推荐的酒店" class="content-card">
      <a-list :data-source="hotels" :grid="{ gutter: 16, column: 2 }">
        <template #renderItem="{ item }">
          <a-list-item>
            <a-card size="small" class="item-card">
              <div class="item-name">{{ item.name }}</div>
              <div class="item-address">{{ item.address }}</div>
            </a-card>
          </a-list-item>
        </template>
      </a-list>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useTripStore } from '@/stores/tripStore'

const store = useTripStore()

const attractions = computed(() => store.streamingData.attractions)
const weather = computed(() => store.streamingData.weather)
const hotels = computed(() => store.streamingData.hotels)
</script>

<style scoped>
.streaming-content {
  margin-top: 24px;
}

.content-card {
  margin-bottom: 16px;
  animation: fadeInUp 0.5s ease;
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

.item-card {
  transition: all 0.3s ease;
}

.item-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.item-name {
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.item-address {
  font-size: 12px;
  color: #999;
}

.weather-card {
  text-align: center;
  background: linear-gradient(135deg, #e3f2fd 0%, #f5f7fa 100%);
}

.weather-date {
  font-size: 12px;
  color: #666;
  margin-bottom: 8px;
}

.weather-temp {
  font-size: 18px;
  font-weight: 600;
  color: #2196f3;
  margin-bottom: 4px;
}

.weather-desc {
  font-size: 14px;
  color: #333;
}

.weather-suggestion {
  margin-top: 8px;
  text-align: left;
}

.suggestion-label {
  font-weight: 600;
  color: #333;
  font-size: 12px;
  margin-bottom: 4px;
}

.suggestion-content {
  font-size: 11px;
  color: #666;
  line-height: 1.5;
  white-space: pre-wrap;
}
</style>
