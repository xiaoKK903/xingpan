import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { userApi, vipApi } from '@/api'
import router from '@/router'

export const useUserStore = defineStore('user', () => {
  const userInfo = ref(null)
  const token = ref(localStorage.getItem('token') || '')
  const vipStatus = ref(null)
  const vipPrivileges = ref([])

  const isLoggedIn = computed(() => !!token.value && !!userInfo.value)
  const username = computed(() => userInfo.value?.username || '')
  const email = computed(() => userInfo.value?.email || '')
  const isAdmin = computed(() => !!userInfo.value?.is_superuser)
  
  const isVip = computed(() => !!vipStatus.value?.is_vip)
  const vipPlanType = computed(() => vipStatus.value?.plan_type || '')
  const vipDaysRemaining = computed(() => vipStatus.value?.days_remaining || 0)
  const vipFreeReportsRemaining = computed(() => vipStatus.value?.free_reports_remaining || 0)
  const hasExclusiveSkin = computed(() => isVip.value && vipPrivileges.value.some(p => p.privilege_key === 'exclusive_skin'))
  const hasNoAds = computed(() => isVip.value && vipPrivileges.value.some(p => p.privilege_key === 'no_ads'))
  const hasUnlimitedSynastry = computed(() => isVip.value && vipPrivileges.value.some(p => p.privilege_key === 'unlimited_synastry'))

  async function login(username, password) {
    const response = await userApi.login(username, password)
    token.value = response.access_token
    userInfo.value = response.user
    localStorage.setItem('token', response.access_token)
    
    await fetchVipStatus()
    
    return response
  }

  async function register(username, password, email) {
    return await userApi.register(username, password, email)
  }

  async function getCurrentUser() {
    try {
      const response = await userApi.getCurrentUser()
      userInfo.value = response
      
      if (token.value) {
        await fetchVipStatus()
      }
      
      return response
    } catch (error) {
      token.value = ''
      userInfo.value = null
      vipStatus.value = null
      vipPrivileges.value = []
      localStorage.removeItem('token')
      throw error
    }
  }

  async function fetchVipStatus() {
    if (!token.value) {
      vipStatus.value = null
      vipPrivileges.value = []
      return
    }
    
    try {
      const response = await vipApi.getMyStatus()
      vipStatus.value = response.vip_status
      vipPrivileges.value = response.privileges || []
    } catch (error) {
      console.error('获取VIP状态失败:', error)
    }
  }

  async function subscribeVip(planType) {
    const response = await vipApi.subscribe(planType)
    return response
  }

  async function cancelAutoRenew() {
    await vipApi.cancelAutoRenew()
    if (vipStatus.value) {
      vipStatus.value.auto_renew_enabled = false
    }
  }

  function checkPrivilege(privilegeKey) {
    if (!isVip.value) return false
    return vipPrivileges.value.some(p => p.privilege_key === privilegeKey)
  }

  function getPrivilegeValue(privilegeKey) {
    if (!isVip.value) return null
    const privilege = vipPrivileges.value.find(p => p.privilege_key === privilegeKey)
    return privilege?.value_data || null
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    vipStatus.value = null
    vipPrivileges.value = []
    localStorage.removeItem('token')
    router.push('/login')
  }

  return {
    userInfo,
    token,
    vipStatus,
    vipPrivileges,
    isLoggedIn,
    username,
    email,
    isAdmin,
    isVip,
    vipPlanType,
    vipDaysRemaining,
    vipFreeReportsRemaining,
    hasExclusiveSkin,
    hasNoAds,
    hasUnlimitedSynastry,
    login,
    register,
    getCurrentUser,
    fetchVipStatus,
    subscribeVip,
    cancelAutoRenew,
    checkPrivilege,
    getPrivilegeValue,
    logout
  }
})
