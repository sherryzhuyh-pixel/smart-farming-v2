import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from '../node_modules/element-plus/dist/index.full.mjs'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import '../node_modules/element-plus/dist/index.css'
import zhCn from '../node_modules/element-plus/dist/locale/zh-cn.mjs'
import App from './App.vue'
import router from './router'
import './styles/variables.css'
import { useAuthStore } from './stores/auth'

const app = createApp(App)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })

// Global fetch interceptor: automatically attach Authorization header
const originalFetch = window.fetch
window.fetch = async function (url, options = {}) {
  const authStore = useAuthStore()
  if (authStore.token) {
    options.headers = {
      ...options.headers,
      Authorization: `Bearer ${authStore.token}`
    }
  }
  return originalFetch(url, options)
}

app.mount('#app')
