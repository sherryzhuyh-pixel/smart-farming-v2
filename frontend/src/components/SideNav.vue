<template>
  <el-aside class="sidebar" width="var(--sidebar-width)">
    <div class="logo">
      <el-icon size="28" color="#409eff"><Chicken /></el-icon>
      <span class="logo-text">智慧养殖 V2.0</span>
    </div>
    <el-menu
      :default-active="$route.path"
      router
      class="sidebar-menu"
      background-color="#001529"
      text-color="#bfcbd9"
      active-text-color="#409eff"
    >
      <el-menu-item v-for="route in menuRoutes" :key="route.path" :index="route.path">
        <el-icon>
          <component :is="route.meta.icon" />
        </el-icon>
        <span>{{ route.meta.title }}</span>
      </el-menu-item>
    </el-menu>
  </el-aside>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import router from '@/router'

const $route = useRoute()
const menuRoutes = computed(() => {
  const layoutRoute = router.getRoutes().find(r => r.path === '/')
  return layoutRoute?.children || []
})
</script>

<style scoped>
.sidebar {
  background-color: #001529;
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.logo {
  height: var(--header-height);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.logo-text {
  color: #fff;
  font-size: 16px;
  font-weight: 600;
}

.sidebar-menu {
  border-right: none;
  flex: 1;
}

.sidebar-menu :deep(.el-menu-item) {
  height: 50px;
  line-height: 50px;
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background-color: #1890ff !important;
}
</style>
