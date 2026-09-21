<template>
  <el-container class="app-layout">
    <SideNav />
    <el-container class="main-container">
      <TopBar />
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import SideNav from './SideNav.vue'
import TopBar from './TopBar.vue'
</script>

<style scoped>
.app-layout {
  height: 100vh;
  width: 100vw;
}

.main-container {
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.main-content {
  padding: 0;
  overflow-y: auto;
  background-color: var(--bg-base);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
