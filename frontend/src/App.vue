<template>
  <div id="app">
    <a-layout style="min-height: 100vh">
      <a-layout-header style="background: #001529; padding: 0 50px; display: flex; justify-content: space-between; align-items: center">
        <router-link to="/" style="text-decoration: none; color: white; font-size: 24px; font-weight: bold; cursor: pointer; transition: opacity 0.3s" 
          @mouseenter="$event.target.style.opacity = '0.8'"
          @mouseleave="$event.target.style.opacity = '1'">
          🌍 智能旅行规划系统
        </router-link>
        <div style="display: flex; align-items: center; gap: 16px">
          <a-button
            v-if="authStore.isAuthenticated"
            type="link"
            @click="goToHistory"
            style="color: white"
          >
            📋 历史记录
          </a-button>
          <a-dropdown v-if="authStore.isAuthenticated" placement="bottomRight">
            <a-button type="link" style="color: white">
              👤 {{ authStore.user?.username || '用户' }}
            </a-button>
            <template #overlay>
              <a-menu>
                <a-menu-item @click="handleLogout">登出</a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
          <a-button
            v-else
            type="link"
            @click="$router.push('/login')"
            style="color: white"
          >
            登录
          </a-button>
        </div>
      </a-layout-header>
      <a-layout-content style="padding: 24px">
        <router-view />
      </a-layout-content>
      <a-layout-footer style="text-align: center">
        智能旅行规划系统 ©2025
      </a-layout-footer>
    </a-layout>
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Modal } from 'ant-design-vue'
import { useAuthStore } from './stores/authStore'
import { useTripStore } from './stores/tripStore'

const router = useRouter()
const authStore = useAuthStore()

// 监听路由变化，确保登录状态正确更新
watch(() => router.currentRoute.value.path, () => {
  // 如果已登录但用户信息丢失，尝试刷新
  if (authStore.token && !authStore.user) {
    authStore.refreshUser()
  }
})

// 组件挂载时检查登录状态
onMounted(() => {
  if (authStore.token && !authStore.user) {
    authStore.refreshUser()
  }
})

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

function goToHistory() {
  // 检查是否有正在进行的请求
  const tripStore = useTripStore()
  if (tripStore.isRequesting) {
    // 如果有正在进行的请求，提示用户
    Modal.confirm({
      title: '确认离开',
      content: '当前正在生成旅行计划，离开页面将中断请求。是否继续？',
      okText: '继续离开',
      cancelText: '取消',
      onOk: () => {
        // 记录当前页面，以便历史记录页面可以返回
        const currentPath = router.currentRoute.value.path
        router.push({ path: '/history', query: { from: currentPath } })
      }
    })
  } else {
    // 记录当前页面，以便历史记录页面可以返回
    const currentPath = router.currentRoute.value.path
    router.push({ path: '/history', query: { from: currentPath } })
  }
}
</script>

<style>
#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    'Noto Sans', sans-serif;
}
</style>

