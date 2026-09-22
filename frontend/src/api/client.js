import axios from 'axios'
import { getToken, TOKEN_KEY, USER_KEY } from '@/stores/auth.js'
import { ElMessage } from 'element-plus'

const client = axios.create({
  baseURL: '/api/v2',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器：自动附加 JWT Token
client.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：统一错误处理 + 分页结构适配
client.interceptors.response.use(
  (response) => {
    const payload = response.data

    // 适配后端分页结构 -> mock 兼容结构
    if (payload.pagination && Array.isArray(payload.data)) {
      return {
        code: payload.code,
        message: payload.message,
        data: {
          list: payload.data,
          pagination: payload.pagination,
        },
      }
    }

    // 单条数据直接透传
    return payload
  },
  (error) => {
    if (error.response) {
      const status = error.response.status
      const msg = error.response.data?.message || '服务器错误'

      if (status === 401) {
        sessionStorage.removeItem(TOKEN_KEY)
        sessionStorage.removeItem(USER_KEY)
        window.location.href = '/login'
      } else if (status >= 500) {
        ElMessage.error(msg)
      } else {
        ElMessage.warning(msg)
      }
    } else {
      ElMessage.error('网络连接失败，请检查网络')
    }
    return Promise.reject(error)
  }
)

export default client
