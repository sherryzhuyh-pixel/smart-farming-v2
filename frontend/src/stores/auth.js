import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const TOKEN_KEY = 'sf_auth_token'
const USER_KEY = 'sf_auth_user'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const user = ref(null)

  try {
    const storedUser = localStorage.getItem(USER_KEY)
    if (storedUser) user.value = JSON.parse(storedUser)
  } catch {
    user.value = null
  }

  const isLoggedIn = computed(() => !!token.value)

  function setAuth(authToken, userInfo) {
    token.value = authToken
    user.value = userInfo
    localStorage.setItem(TOKEN_KEY, authToken)
    localStorage.setItem(USER_KEY, JSON.stringify(userInfo))
  }

  function clearAuth() {
    token.value = ''
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }

  return { token, user, isLoggedIn, setAuth, clearAuth }
})
