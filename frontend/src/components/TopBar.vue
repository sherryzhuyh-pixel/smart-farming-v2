<template>
  <el-header class="top-bar">
    <div class="breadcrumb">
      <el-breadcrumb>
        <el-breadcrumb-item>AI智慧养殖系统</el-breadcrumb-item>
        <el-breadcrumb-item>{{ $route.meta?.title }}</el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <div class="user-area">
      <el-badge :value="3" class="message-badge">
        <el-icon size="20"><Bell /></el-icon>
      </el-badge>
      <el-dropdown @command="handleCommand">
        <span class="user-info">
          <el-avatar :size="32" :icon="UserFilled" />
          <span class="user-name">{{ displayName }}</span>
          <el-icon><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">个人中心</el-dropdown-item>
            <el-dropdown-item command="settings">系统设置</el-dropdown-item>
            <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </el-header>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { UserFilled, Bell, ArrowDown } from '@element-plus/icons-vue'

const $route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const displayName = computed(() => authStore.user?.displayName || authStore.user?.username || '用户')

function handleCommand(cmd) {
  if (cmd === 'logout') {
    authStore.clearAuth()
    router.push('/login')
    ElMessage.success('已退出登录')
  }
}
</script>

<style scoped>
.top-bar {
  height: var(--header-height);
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  z-index: 10;
}

.user-area {
  display: flex;
  align-items: center;
  gap: 20px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.user-name {
  font-size: 14px;
  color: var(--text-primary);
}

.message-badge {
  cursor: pointer;
}
</style>
