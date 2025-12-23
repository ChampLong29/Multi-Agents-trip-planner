import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia } from 'pinia'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import App from './App.vue'
import Home from './views/Home.vue'
import Result from './views/Result.vue'
import Login from './views/Login.vue'
import History from './views/History.vue'
import { useAuthStore } from './stores/authStore'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Home',
      component: Home
    },
    {
      path: '/result',
      name: 'Result',
      component: Result
    },
    {
      path: '/login',
      name: 'Login',
      component: Login
    },
    {
      path: '/history',
      name: 'History',
      component: History,
      meta: { requiresAuth: true }
    }
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

const pinia = createPinia()
const app = createApp(App)

app.use(pinia)
app.use(router)
app.use(Antd)

// 应用启动时检查并刷新用户状态
const authStore = useAuthStore()
if (authStore.token) {
  // 如果有token，尝试刷新用户信息
  authStore.refreshUser().catch(() => {
    // 如果刷新失败，清除无效的token
    authStore.logout()
  })
}

app.mount('#app')

