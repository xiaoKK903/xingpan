import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { userApi } from '@/api'
import router from '@/router'

export const useUserStore = defineStore('user', () => {
  const userInfo = ref(null)
  const token = ref(localStorage.getItem('token') || '')

  const isLoggedIn = computed(() => !!token.value && !!userInfo.value)
  const username = computed(() => userInfo.value?.username || '')
  const email = computed(() => userInfo.value?.email || '')
  const isAdmin = computed(() => !!userInfo.value?.is_superuser)

  async function login(username, password) {
    const response = await userApi.login(username, password)
    token.value = response.access_token
    userInfo.value = response.user
    localStorage.setItem('token', response.access_token)
    return response
  }

  async function register(username, password, email) {
    return await userApi.register(username, password, email)
  }

  async function getCurrentUser() {
    try {
      const response = await userApi.getCurrentUser()
      userInfo.value = response
      return response
    } catch (error) {
      token.value = ''
      userInfo.value = null
      localStorage.removeItem('token')
      throw error
    }
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
    router.push('/login')
  }

  return {
    userInfo,
    token,
    isLoggedIn,
    username,
    email,
    isAdmin,
    login,
    register,
    getCurrentUser,
    logout
  }
})
