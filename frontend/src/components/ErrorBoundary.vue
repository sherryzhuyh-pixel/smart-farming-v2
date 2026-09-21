<template>
  <div v-if="hasError" class="error-boundary">
    <el-result icon="error" title="页面渲染出错" :sub-title="errorMessage">
      <template #extra>
        <el-button type="primary" @click="reload">重新加载</el-button>
        <el-button @click="goHome">返回首页</el-button>
      </template>
    </el-result>
  </div>
  <slot v-else />
</template>

<script setup>
import { ref, onErrorCaptured } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const hasError = ref(false)
const errorMessage = ref('')

onErrorCaptured((err) => {
  hasError.value = true
  errorMessage.value = err?.message || '未知错误'
  console.error('[ErrorBoundary]', err)
  return false
})

function reload() {
  window.location.reload()
}

function goHome() {
  hasError.value = false
  errorMessage.value = ''
  router.push('/')
}
</script>

<style scoped>
.error-boundary {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
