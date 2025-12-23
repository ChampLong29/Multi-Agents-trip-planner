<template>
  <div class="login-container">
    <div class="login-card">
      <h1 class="title">智能旅行规划系统</h1>
      
      <a-tabs v-model:activeKey="activeTab" class="login-tabs">
        <a-tab-pane key="login" tab="登录">
          <a-form
            :model="loginForm"
            :rules="loginRules"
            @finish="handleLogin"
            layout="vertical"
          >
            <a-form-item name="username" label="用户名或邮箱">
              <a-input
                v-model:value="loginForm.username"
                placeholder="请输入用户名或邮箱"
                size="large"
              />
            </a-form-item>
            
            <a-form-item name="password" label="密码">
              <a-input-password
                v-model:value="loginForm.password"
                placeholder="请输入密码"
                size="large"
              />
            </a-form-item>
            
            <a-form-item>
              <a-button
                type="primary"
                html-type="submit"
                size="large"
                block
                :loading="loading"
              >
                登录
              </a-button>
            </a-form-item>
          </a-form>
        </a-tab-pane>
        
        <a-tab-pane key="register" tab="注册">
          <a-form
            :model="registerForm"
            :rules="registerRules"
            @finish="handleRegister"
            layout="vertical"
          >
            <a-form-item name="username" label="用户名">
              <a-input
                v-model:value="registerForm.username"
                placeholder="请输入用户名（3-50个字符）"
                size="large"
              />
            </a-form-item>
            
            <a-form-item name="email" label="邮箱">
              <a-input
                v-model:value="registerForm.email"
                placeholder="请输入邮箱"
                size="large"
              />
            </a-form-item>
            
            <a-form-item name="password" label="密码">
              <a-input-password
                v-model:value="registerForm.password"
                placeholder="请输入密码（至少6个字符）"
                size="large"
              />
            </a-form-item>
            
            <a-form-item name="confirmPassword" label="确认密码">
              <a-input-password
                v-model:value="registerForm.confirmPassword"
                placeholder="请再次输入密码"
                size="large"
              />
            </a-form-item>
            
            <a-form-item>
              <a-button
                type="primary"
                html-type="submit"
                size="large"
                block
                :loading="loading"
              >
                注册
              </a-button>
            </a-form-item>
          </a-form>
        </a-tab-pane>
      </a-tabs>
      
      <a-alert
        v-if="errorMessage"
        :message="errorMessage"
        type="error"
        show-icon
        closable
        @close="errorMessage = ''"
        style="margin-top: 16px"
      />
      
      <a-alert
        v-if="successMessage"
        :message="successMessage"
        type="success"
        show-icon
        closable
        @close="successMessage = ''"
        style="margin-top: 16px"
      />
      
      <!-- 返回首页按钮 -->
      <div style="margin-top: 24px; text-align: center">
        <a-button type="link" @click="goHome" style="color: #667eea">
          ← 返回首页
        </a-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/stores/authStore'

const router = useRouter()
const authStore = useAuthStore()

const activeTab = ref('login')
const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const loginForm = reactive({
  username: '',
  password: ''
})

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const loginRules = {
  username: [
    { required: true, message: '请输入用户名或邮箱', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

const validateConfirmPassword = (_rule: any, value: string) => {
  if (!value) {
    return Promise.reject('请确认密码')
  }
  if (value !== registerForm.password) {
    return Promise.reject('两次输入的密码不一致')
  }
  return Promise.resolve()
}

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度为3-50个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

async function handleLogin() {
  loading.value = true
  errorMessage.value = ''
  
  try {
    const result = await authStore.login(loginForm.username, loginForm.password)
    
    if (result.success) {
      message.success('登录成功')
      
      // 确保状态已更新，等待一下让 Vue 响应式系统更新
      await new Promise(resolve => setTimeout(resolve, 100))
      
      // 检查是否有重定向参数
      const redirect = router.currentRoute.value.query.redirect as string
      router.push(redirect || '/')
    } else {
      errorMessage.value = result.message || '登录失败'
    }
  } catch (error: any) {
    errorMessage.value = error.message || '登录失败'
  } finally {
    loading.value = false
  }
}

function goHome() {
  router.push('/')
}

async function handleRegister() {
  loading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  
  try {
    const result = await authStore.register(
      registerForm.username,
      registerForm.email,
      registerForm.password
    )
    
    if (result.success) {
      successMessage.value = result.message || '注册成功'
      // 切换到登录标签页
      setTimeout(() => {
        activeTab.value = 'login'
        loginForm.username = registerForm.username
      }, 1500)
    } else {
      errorMessage.value = result.message || '注册失败'
    }
  } catch (error: any) {
    errorMessage.value = error.message || '注册失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 450px;
  background: white;
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.title {
  text-align: center;
  font-size: 28px;
  font-weight: 700;
  color: #333;
  margin-bottom: 32px;
}

.login-tabs :deep(.ant-tabs-tab) {
  font-size: 16px;
  font-weight: 500;
}

.login-tabs :deep(.ant-tabs-content) {
  margin-top: 24px;
}
</style>

