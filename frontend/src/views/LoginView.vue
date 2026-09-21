<template>
  <div class="login-page">
    <el-card class="login-card" shadow="always">
      <template #header>
        <div class="login-header">
          <el-icon size="48" color="#409eff"><Chicken /></el-icon>
          <h2>AI智慧养殖系统 V2.0</h2>
          <p>请登录以继续使用</p>
        </div>
      </template>
      <el-form :model="form" :rules="rules" ref="formRef" label-position="top">
        <el-form-item label="账号" prop="username">
          <el-input v-model="form.username" placeholder="请输入账号" prefix-icon="User" @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" prefix-icon="Lock" show-password @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" style="width: 100%;" size="large" :loading="loading" @click="handleLogin">登录</el-button>
        </el-form-item>
      </el-form>
      <div class="login-tip">
        <el-text type="info" size="small">演示账号：admin / admin123</el-text>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Chicken } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref(null)
const loading = ref(false)

const form = ref({ username: '', password: '' })

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  // Demo authentication - in production, replace with real API call
  if (form.value.username === 'admin' && form.value.password === 'admin123') {
    authStore.setAuth('demo-jwt-token-' + Date.now(), {
      username: form.value.username,
      displayName: '场长',
      role: 'admin'
    })
    ElMessage.success('登录成功')
    router.push('/')
  } else {
    ElMessage.error('账号或密码错误')
  }
  loading.value = false
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  width: 100vw;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e7ed 100%);
}
.login-card {
  width: 420px;
}
.login-header {
  text-align: center;
}
.login-header h2 {
  margin: 12px 0 4px;
  font-size: 22px;
  color: #303133;
}
.login-header p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}
.login-tip {
  text-align: center;
  margin-top: 12px;
}
</style>
