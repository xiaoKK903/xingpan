import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

const request = axios.create({
  baseURL: '/api',
  timeout: 30000
})

request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    if (!(config.data instanceof FormData) && 
        config.method !== 'get' && 
        !config.headers['Content-Type']) {
      config.headers['Content-Type'] = 'application/json'
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

request.interceptors.response.use(
  (response) => {
    const { data } = response
    if (data.code === 200 || data.code === 201) {
      return 'data' in data ? data.data : data
    }
    ElMessage.error(data.message || '请求失败')
    return Promise.reject(new Error(data.message || '请求失败'))
  },
  (error) => {
    const originalRequest = error.config
    
    if (error.response) {
      switch (error.response.status) {
        case 401:
          if (!originalRequest._retry) {
            if (isRefreshing) {
              return new Promise(function(resolve, reject) {
                failedQueue.push({ resolve, reject })
              }).then(token => {
                originalRequest.headers.Authorization = 'Bearer ' + token
                return request(originalRequest)
              }).catch(err => {
                return Promise.reject(err)
              })
            }
            
            originalRequest._retry = true
            isRefreshing = true
            
            localStorage.removeItem('token')
            
            const currentPath = router.currentRoute.value.path
            const isLoginPage = currentPath === '/login' || currentPath === '/register'
            const isPublicPage = currentPath === '/astro' || currentPath === '/'
            
            if (!isLoginPage && !isPublicPage) {
              ElMessage.error('登录已过期，请重新登录')
              router.push('/login')
            }
            
            processQueue(error, null)
            isRefreshing = false
          }
          return Promise.reject(error)
          
        case 403:
          ElMessage.error('没有权限访问')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          ElMessage.error('服务器错误')
          break
        case 422:
          const detail422 = error.response.data?.detail
          let errorMessage = '参数校验失败'
          if (Array.isArray(detail422) && detail422.length > 0) {
            const firstError = detail422[0]
            errorMessage = firstError.msg || firstError.message || '参数校验失败'
          } else if (typeof detail422 === 'string') {
            errorMessage = detail422
          }
          ElMessage.error(errorMessage)
          break
        default:
          let defaultMessage = error.message || '请求失败'
          const defaultDetail = error.response.data?.detail
          if (typeof defaultDetail === 'string') {
            defaultMessage = defaultDetail
          } else if (Array.isArray(defaultDetail) && defaultDetail.length > 0 && typeof defaultDetail[0] === 'object') {
            defaultMessage = defaultDetail[0].msg || defaultDetail[0].message || '参数校验失败'
          }
          ElMessage.error(defaultMessage)
      }
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }
    return Promise.reject(error)
  }
)

export const userApi = {
  login(username, password) {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    return request.post('/users/login', formData)
  },
  
  register(username, password, email, inviteCode = null) {
    const data = {
      username,
      password,
      email
    }
    if (inviteCode) {
      data.invite_code = inviteCode
    }
    return request.post('/users/register', data)
  },
  
  getCurrentUser() {
    return request.get('/users/me')
  },
  
  updateProfile(data) {
    return request.put('/users/me', data)
  }
}

export const conversationApi = {
  getList(params = {}) {
    return request.get('/conversations/', { params })
  },
  
  getById(id) {
    return request.get(`/conversations/${id}`)
  },
  
  create(data) {
    return request.post('/conversations/', data)
  },
  
  update(id, data) {
    return request.put(`/conversations/${id}`, data)
  },
  
  delete(id) {
    return request.delete(`/conversations/${id}`)
  }
}

export const messageApi = {
  getByConversationId(conversationId, params = {}) {
    return request.get(`/messages/conversation/${conversationId}`, { params })
  },
  
  getById(id) {
    return request.get(`/messages/${id}`)
  },
  
  create(data) {
    return request.post('/messages/', data)
  },
  
  delete(id) {
    return request.delete(`/messages/${id}`)
  }
}

export const chatApi = {
  send(data) {
    return request.post('/chat/', data)
  }
}

export const astroApi = {
  calculateChart(data) {
    return request.post('/astro/calculate', data)
  },
  getHouseSystems() {
    return request.get('/astro/systems')
  },
  getPlanets() {
    return request.get('/astro/planets')
  },
  getZodiacSigns() {
    return request.get('/astro/zodiac-signs')
  }
}

export const geoApi = {
  searchCity(query) {
    return request.get('/geo/search', {
      params: { query, limit: 10 }
    })
  },
  geocodeCity(city) {
    return request.get('/geo/geocode', {
      params: { city }
    })
  }
}

export const chartApi = {
  saveChart(data) {
    return request.post('/charts', data)
  },
  getMyCharts(params = {}) {
    return request.get('/charts', { params })
  },
  getChartById(id) {
    return request.get(`/charts/${id}`)
  },
  updateChart(id, data) {
    return request.put(`/charts/${id}`, data)
  },
  deleteChart(id) {
    return request.delete(`/charts/${id}`)
  }
}

export const reportApi = {
  getInterpretation(chartId) {
    return request.get(`/reports/interpretation/${chartId}`)
  },
  getPdfReport(chartId, template = 'detailed') {
    return request.get(`/reports/pdf/${chartId}`, {
      params: { template },
      responseType: 'blob'
    })
  },
  generatePdfDirect(chartInput, template = 'detailed') {
    return request.post('/reports/pdf/generate', chartInput, {
      params: { template },
      responseType: 'blob'
    })
  },
  generateInterpretationDirect(chartInput) {
    return request.post('/reports/interpretation/generate', chartInput)
  },
  generatePdfWithInterpretation(chartInput, template = 'detailed') {
    return request.post('/reports/pdf/generate-with-interpretation', chartInput, {
      params: { template }
    })
  },
  getTemplates() {
    return request.get('/reports/templates')
  }
}

export const synastryApi = {
  calculateSynastry(data) {
    return request.post('/synastry/calculate', data)
  },
  testSynastry() {
    return request.get('/synastry/test')
  },
  calculateAndAnalyze(data) {
    return request.post('/synastry-analysis/calculate-and-analyze', data)
  },
  saveRecord(data) {
    return request.post('/synastry-analysis/save', data)
  },
  getList(params = {}) {
    return request.get('/synastry-analysis/list', { params })
  },
  getById(id) {
    return request.get(`/synastry-analysis/${id}`)
  },
  update(id, data) {
    return request.put(`/synastry-analysis/${id}`, data)
  },
  delete(id) {
    return request.delete(`/synastry-analysis/${id}`)
  },
  generateShare(id) {
    return request.post(`/synastry-analysis/${id}/generate-share`)
  },
  getByShareCode(shareCode) {
    return request.get(`/synastry-analysis/share/${shareCode}`)
  }
}

export const aiInterpretationApi = {
  generateInterpretation(data) {
    return request.post('/ai/interpret', data)
  },
  generateInterpretationDirect(data) {
    return request.post('/ai/interpret/direct', data)
  },
  checkHealth() {
    return request.get('/ai/health')
  },
  testConnection(data) {
    return request.post('/ai/test', data)
  }
}

export const horoscopeApi = {
  getDailyHoroscope(sign, date = null) {
    const params = { sign }
    if (date) {
      params.date = date
    }
    return request.get('/horoscope/today', { params })
  },
  getPersonalHoroscope(date = null) {
    const params = {}
    if (date) {
      params.date = date
    }
    return request.get('/horoscope/personal', { params })
  },
  getZodiacSigns() {
    return request.get('/horoscope/signs')
  }
}

export const transitApi = {
  calculateTransit(data) {
    return request.post('/transit/calculate', data)
  },
  get7DayTrend(data) {
    return request.post('/transit/trend', data)
  },
  getAIInterpretation(data) {
    return request.post('/transit/interpret', data)
  },
  getPersonalTransit(targetDate = null) {
    const params = {}
    if (targetDate) {
      params.target_date = targetDate
    }
    return request.get('/transit/personal', { params })
  },
  getPersonalTrend(startDate = null) {
    const params = {}
    if (startDate) {
      params.start_date = startDate
    }
    return request.get('/transit/personal/trend', { params })
  }
}

export const groupMatrixApi = {
  calculate(data) {
    return request.post('/group-matrix/calculate', data)
  },
  simulateScenario(matrixData, scenarioType) {
    return request.post('/group-matrix/simulate-scenario', matrixData, {
      params: { scenario_type: scenarioType }
    })
  },
  getScenarioTypes() {
    return request.get('/group-matrix/scenario-types')
  },
  getRoleTypes() {
    return request.get('/group-matrix/role-types')
  }
}

export const lifeScriptApi = {
  analyzeYear(data) {
    return request.post('/life-script/analyze', data)
  },
  generateScript(data) {
    return request.post('/life-script/generate-script', data, {
      timeout: 180000
    })
  },
  analyzeRange(data) {
    return request.post('/life-script/analyze-range', data)
  },
  getKeyYears(data) {
    return request.post('/life-script/key-years', data)
  },
  getPersonalAnalysis(targetYear) {
    return request.get('/life-script/personal/analyze', {
      params: { target_year: targetYear }
    })
  },
  getPersonalScript(targetYear) {
    return request.get('/life-script/personal/generate-script', {
      params: { target_year: targetYear },
      timeout: 180000
    })
  }
}

export const workbenchApi = {
  calculateChart(data) {
    return request.post('/workbench/calculate', data)
  },
  
  adjustPlanet(data) {
    return request.post('/workbench/adjust-planet', data)
  },
  
  probePlanet(data) {
    return request.post('/workbench/probe-planet', data)
  },
  
  generateNotes(data) {
    return request.post('/workbench/generate-notes', data)
  },
  
  getClassicalRules() {
    return request.get('/workbench/classical-rules')
  },
  
  getPlanetsInfo() {
    return request.get('/workbench/planets-info')
  }
}

export const plazaApi = {
  getStyles() {
    return request.get('/plaza/styles')
  },
  
  analyzeConflict(data) {
    return request.post('/plaza/analyze-conflict', data)
  },
  
  encounter(data) {
    return request.post('/plaza/encounter', data)
  },
  
  testEncounter() {
    return request.post('/plaza/test-encounter')
  },
  
  getWeatherPanel() {
    return request.get('/plaza/weather-panel')
  },
  
  getPlazaMissions() {
    return request.get('/plaza/plaza-missions')
  },
  
  simulateOminous(eventKey, durationMinutes = 30) {
    return request.post('/plaza/simulate-ominous', {
      event_key: eventKey,
      duration_minutes: durationMinutes
    })
  },
  
  clearSimulatedOminous() {
    return request.post('/plaza/clear-simulated-ominous')
  },
  
  getSimulatedStatus() {
    return request.get('/plaza/simulated-status')
  },
  
  getWeatherHistory(hours = 12) {
    return request.get('/plaza/weather-history', { params: { hours } })
  },
  
  getOminousInfo() {
    return request.get('/plaza/ominous-info')
  }
}

export const energyWeatherApi = {
  getCurrentWeather() {
    return request.get('/energy-weather/current')
  },
  
  getWeatherHistory(hours = 12) {
    return request.get('/energy-weather/history', { params: { hours } })
  },
  
  getMissions() {
    return request.get('/energy-weather/missions')
  },
  
  completeMission(missionInstanceId, completedActions = null, proofText = null) {
    return request.post('/energy-weather/missions/complete', {
      mission_instance_id: missionInstanceId,
      completed_actions: completedActions,
      proof_text: proofText
    })
  },
  
  getContributionTypes() {
    return request.get('/energy-weather/contribution-types')
  },
  
  contributeEnergy(contributionType) {
    return request.post('/energy-weather/contribute', {
      contribution_type: contributionType
    })
  },
  
  getMyCompletions(limit = 20) {
    return request.get('/energy-weather/my-completions', { params: { limit } })
  },
  
  getMissionCompletions(params = {}) {
    const limit = params.limit || 20
    return request.get('/energy-weather/my-completions', { params: { limit } })
  },
  
  getMyTransactions(currencyType = null, limit = 20) {
    const params = { limit }
    if (currencyType) params.currency_type = currencyType
    return request.get('/energy-weather/my-transactions', { params })
  },
  
  getTransactionHistory(params = {}) {
    const limit = params.limit || 20
    return request.get('/energy-weather/my-transactions', { params: { limit } })
  },
  
  getOminousEvents() {
    return request.get('/energy-weather/ominous-events')
  },
  
  getMissionTemplates(moodType = null) {
    const params = {}
    if (moodType) params.mood_type = moodType
    return request.get('/energy-weather/mission-templates', { params })
  },
  
  getWeatherLevels() {
    return request.get('/energy-weather/weather-levels')
  },
  
  refreshWeather() {
    return request.post('/energy-weather/refresh')
  }
}

export const starResonanceApi = {
  getPoolStatus() {
    return request.get('/star-resonance/status')
  },
  
  getMyStrongPlanets() {
    return request.get('/star-resonance/my-strong-planets')
  },
  
  refinePreview(params) {
    return request.post('/star-resonance/refine', params)
  },
  
  contribute(params) {
    return request.post('/star-resonance/contribute', params)
  },
  
  getMyTickets(onlyValid = true, limit = 20) {
    return request.get('/star-resonance/my-tickets', { 
      params: { only_valid: onlyValid, limit } 
    })
  },
  
  getRecentContributions(limit = 20) {
    return request.get('/star-resonance/recent-contributions', { 
      params: { limit } 
    })
  },
  
  getElementInfo() {
    return request.get('/star-resonance/element-info')
  }
}

export const bossBattleApi = {
  getHall() {
    return request.get('/boss-battle/hall')
  },
  
  getActiveBosses() {
    return request.get('/boss-battle/bosses')
  },
  
  getBossDetail(bossId) {
    return request.get(`/boss-battle/bosses/${bossId}`)
  },
  
  createTeam(data) {
    return request.post('/boss-battle/teams/create', data)
  },
  
  inviteFromEncounter(data) {
    return request.post('/boss-battle/teams/invite-from-encounter', data)
  },
  
  addTeamMember(data) {
    return request.post('/boss-battle/teams/add-member', data)
  },
  
  removeTeamMember(teamId, memberId) {
    return request.delete(`/boss-battle/teams/${teamId}/members/${memberId}`)
  },
  
  getTeamDetail(teamId) {
    return request.get(`/boss-battle/teams/${teamId}`)
  },
  
  leaveTeam(memberId) {
    return request.post(`/boss-battle/teams/leave?member_id=${memberId}`)
  },
  
  getMemberCurrentTeam(memberId) {
    return request.get(`/boss-battle/teams/member/${memberId}/current`)
  },
  
  getTeamsByBoss(bossId) {
    return request.get(`/boss-battle/teams/by-boss/${bossId}`)
  },
  
  startBattle(data) {
    return request.post('/boss-battle/battle/start', data)
  },
  
  getBattleResult(battleId) {
    return request.get(`/boss-battle/battle/result/${battleId}`)
  },
  
  autoMatch(bossId, element = null) {
    const params = {}
    if (element) params.element = element
    return request.get(`/boss-battle/match/auto-match/${bossId}`, { params })
  }
}

export const predictionApi = {
  getThemes() {
    return request.get('/prediction/themes')
  },
  
  getUpcoming(includeAnnounced = true) {
    return request.get('/prediction/upcoming', { 
      params: { include_announced: includeAnnounced } 
    })
  },
  
  getOpen() {
    return request.get('/prediction/open')
  },
  
  getDetail(predictionId) {
    return request.get(`/prediction/detail-optimized/${predictionId}`)
  },
  
  validateVote(predictionId, useAsset = 'fragment') {
    return request.get('/prediction/validate-vote', { 
      params: { prediction_id: predictionId, use_asset: useAsset } 
    })
  },
  
  castVoteSecure(data) {
    return request.post('/prediction/vote-secure', data)
  },
  
  claimReward(voteId) {
    return request.post('/prediction/claim-reward', null, {
      params: { vote_id: voteId }
    })
  },
  
  checkRateLimit(actionType = 'vote') {
    return request.get('/prediction/check-rate-limit', {
      params: { action_type: actionType }
    })
  },
  
  getTieredCosts(predictionId) {
    return request.get(`/prediction/tiered-costs/${predictionId}`)
  },
  
  getMyHistory(limit = 20) {
    return request.get('/prediction/my-history', { 
      params: { limit } 
    })
  },
  
  getMyTags(categories = null) {
    const params = {}
    if (categories) params.categories = categories
    return request.get('/prediction/my-tags', { params })
  }
}

export const elementQuestApi = {
  getMyProfile() {
    return request.get('/element-quest/profile/me')
  },
  
  analyzeElements() {
    return request.post('/element-quest/analyze')
  },
  
  analyzeElementsTemporary(chartData) {
    return request.post('/element-quest/analyze-temporary', chartData)
  },
  
  getMyTags() {
    return request.get('/element-quest/tags/me')
  },
  
  getQuestStatus() {
    return request.get('/element-quest/quest/status')
  },
  
  createBlindBox() {
    return request.post('/element-quest/quest/blind-box')
  },
  
  getMyBlindBoxes(status = null) {
    const params = {}
    if (status) params.status = status
    return request.get('/element-quest/quest/blind-boxes', { params })
  },
  
  getBlindBoxDetail(boxId) {
    return request.get(`/element-quest/quest/blind-box/${boxId}`)
  },
  
  revealBlindBox(boxId) {
    return request.post(`/element-quest/quest/blind-box/${boxId}/reveal`)
  },
  
  claimBlindBoxReward(boxId) {
    return request.post(`/element-quest/quest/blind-box/${boxId}/claim`)
  },
  
  refreshQuestCount() {
    return request.post('/element-quest/quest/refresh')
  },
  
  getQuestHistory(limit = 20) {
    return request.get('/element-quest/quest/history', { params: { limit } })
  }
}

export const phaseConnectApi = {
  getMyStatus() {
    return request.get('/phase-connect/my-status')
  },
  
  searchMatches(data) {
    return request.post('/phase-connect/search-matches', data)
  },
  
  startConnection(data) {
    return request.post('/phase-connect/start-connection', data)
  },
  
  getRecentConnections() {
    return request.get('/phase-connect/recent-connections')
  }
}

export const networkChainApi = {
  getMyProfile() {
    return request.get('/network-chain/my-profile')
  },
  
  getRecommendations(type = 'emotional') {
    return request.get('/network-chain/recommendations', { params: { type } })
  },
  
  getDetail(data) {
    return request.post('/network-chain/get-detail', data)
  },
  
  getNetworkGraph() {
    return request.get('/network-chain/network-graph')
  },
  
  addToNetwork(userId) {
    return request.post('/network-chain/add-to-network', { target_user_id: userId })
  }
}

export const synastryEnhancedApi = {
  generateAiCopy(data) {
    return request.post('/synastry-enhanced/generate-ai-copy', data)
  },
  
  generatePhotocard(data) {
    return request.post('/synastry-enhanced/generate-photocard', data)
  },
  
  getEnhancedAnalysis(data) {
    return request.post('/synastry-enhanced/enhanced-analysis', data)
  }
}

export const privateChatApi = {
  startChat(data) {
    return request.post('/private-chat/start', data)
  },
  
  sendMessage(data) {
    return request.post('/private-chat/send', data)
  },
  
  getChatList(skip = 0, limit = 20) {
    return request.get('/private-chat/list', { params: { skip, limit } })
  },
  
  getMessages(chatId, beforeId = null, limit = 50, markAsRead = true) {
    const params = { limit, mark_as_read: markAsRead }
    if (beforeId) params.before_id = beforeId
    return request.get(`/private-chat/${chatId}/messages`, { params })
  },
  
  markAsRead(chatId) {
    return request.post(`/private-chat/${chatId}/read`)
  },
  
  getUnreadCount() {
    return request.get('/private-chat/unread/count')
  }
}

export const photocardApi = {
  savePhotocard(data) {
    return request.post('/photocard/save', data)
  },
  
  getList(skip = 0, limit = 20) {
    return request.get('/photocard/list', { params: { skip, limit } })
  },
  
  getDetail(photocardId, includeSvg = false) {
    return request.get(`/photocard/${photocardId}`, { params: { include_svg: includeSvg } })
  },
  
  sharePhotocard(photocardId) {
    return request.post('/photocard/share', { photocard_id: photocardId })
  },
  
  getShared(shareCode) {
    return request.get(`/photocard/share/${shareCode}`)
  },
  
  deletePhotocard(photocardId) {
    return request.delete(`/photocard/${photocardId}`)
  }
}

export const vipApi = {
  getPlans() {
    return request.get('/vip/plans')
  },
  
  getPrivileges() {
    return request.get('/vip/privileges')
  },
  
  getMyStatus() {
    return request.get('/vip/status')
  },
  
  subscribe(planType) {
    return request.post('/vip/subscribe', null, { params: { plan_type: planType } })
  },
  
  cancelAutoRenew() {
    return request.post('/vip/auto-renew/cancel')
  },
  
  getSubscriptions(limit = 20, offset = 0) {
    return request.get('/vip/subscriptions', { params: { limit, offset } })
  },
  
  checkPrivilege(privilegeKey) {
    return request.get(`/vip/check-privilege/${privilegeKey}`)
  }
}

export const giftApi = {
  getShop() {
    return request.get('/gifts/shop')
  },
  
  sendGift(data) {
    return request.post('/gifts/send', data)
  },
  
  getReceived(limit = 50, offset = 0) {
    return request.get('/gifts/received', { params: { limit, offset } })
  },
  
  getSent(limit = 50, offset = 0) {
    return request.get('/gifts/sent', { params: { limit, offset } })
  },
  
  getDisplayed() {
    return request.get('/gifts/displayed')
  },
  
  displayGift(transactionId, isFeatured = false) {
    return request.post(`/gifts/display/${transactionId}`, null, { params: { is_featured: isFeatured } })
  },
  
  removeDisplayed(displayId) {
    return request.delete(`/gifts/display/${displayId}`)
  },
  
  setFeatured(displayId, isFeatured = true) {
    return request.put(`/gifts/display/${displayId}/featured`, null, { params: { is_featured: isFeatured } })
  },
  
  getStatistics() {
    return request.get('/gifts/statistics')
  },
  
  getUserDisplayedGifts(userId) {
    return request.get(`/gifts/user/${userId}/displayed`)
  }
}

export const reportShopApi = {
  getShop() {
    return request.get('/report-shop/shop')
  },
  
  purchaseReport(data) {
    return request.post('/report-shop/purchase', data)
  },
  
  getPurchased(limit = 20, offset = 0) {
    return request.get('/report-shop/purchased', { params: { limit, offset } })
  },
  
  viewReport(purchaseId) {
    return request.get(`/report-shop/view/${purchaseId}`)
  },
  
  checkAccess(productKey, chartId = null, synastryRecordId = null, groupMatrixId = null) {
    const params = { product_key: productKey }
    if (chartId) params.chart_id = chartId
    if (synastryRecordId) params.synastry_record_id = synastryRecordId
    if (groupMatrixId) params.group_matrix_id = groupMatrixId
    return request.get('/report-shop/check-access', { params })
  },
  
  getStatistics() {
    return request.get('/report-shop/statistics')
  }
}

export const paymentApi = {
  createOrder(data) {
    return request.post('/payment/order/create', data)
  },
  
  getOrder(orderNo) {
    return request.get(`/payment/order/${orderNo}`)
  },
  
  getOrders(status = null, limit = 20, offset = 0) {
    const params = { limit, offset }
    if (status) params.status = status
    return request.get('/payment/orders', { params })
  },
  
  cancelOrder(orderNo) {
    return request.post(`/payment/order/${orderNo}/cancel`)
  },
  
  simulatePayment(orderNo, success = true) {
    return request.post('/payment/sandbox/simulate', { order_no: orderNo, success })
  },
  
  quickPay(orderNo, success = true) {
    return request.get('/payment/sandbox/quick-pay', { params: { order_no: orderNo, success } })
  },
  
  getStatistics() {
    return request.get('/payment/statistics')
  }
}

export const checkinApi = {
  getStatus() {
    return request.get('/checkin/status')
  },
  
  performCheckin() {
    return request.post('/checkin/sign')
  },
  
  getRewards() {
    return request.get('/checkin/rewards')
  },
  
  getHistory(page = 1, pageSize = 20) {
    return request.get('/checkin/history', { params: { page, page_size: pageSize } })
  },
  
  initRewards() {
    return request.post('/checkin/init-rewards')
  }
}

export const inviteApi = {
  getCode() {
    return request.get('/invite/code')
  },
  
  getStats() {
    return request.get('/invite/stats')
  },
  
  getRewards(limit = 20, offset = 0) {
    return request.get('/invite/rewards', { params: { limit, offset } })
  },
  
  recordShare(shareType = 'link', sharePlatform = null) {
    const params = { share_type: shareType }
    if (sharePlatform) {
      params.share_platform = sharePlatform
    }
    return request.post('/invite/share', null, { params })
  },
  
  recordSynastryShare(synastryRecordId, sharePlatform = null) {
    const params = { synastry_record_id: synastryRecordId }
    if (sharePlatform) {
      params.share_platform = sharePlatform
    }
    return request.post('/invite/synastry-share', null, { params })
  },
  
  validateCode(inviteCode) {
    return request.get('/invite/validate-code', { params: { invite_code: inviteCode } })
  },
  
  getMyInvitees(page = 1, pageSize = 20) {
    return request.get('/invite/my-invitees', { params: { page, page_size: pageSize } })
  },
  
  getRules() {
    return request.get('/invite/rules')
  }
}

export const activityApi = {
  getHallActivities() {
    return request.get('/activity/hall')
  },
  
  getActiveBenefits(moduleType = null) {
    const params = {}
    if (moduleType) params.module_type = moduleType
    return request.get('/activity/benefits/active', { params })
  },
  
  calculateBenefits(moduleType, userZodiacSign = null) {
    const params = { module_type: moduleType }
    if (userZodiacSign) params.user_zodiac_sign = userZodiacSign
    return request.get('/activity/benefits/calculate', { params })
  },
  
  getList(statusFilter = null, activityType = null, includeArchived = false) {
    const params = { include_archived: includeArchived }
    if (statusFilter) params.status_filter = statusFilter
    if (activityType) params.activity_type = activityType
    return request.get('/activity/list', { params })
  },
  
  getDetail(activityId) {
    return request.get(`/activity/${activityId}`)
  },
  
  create(data) {
    return request.post('/activity/create', data)
  },
  
  update(activityId, data) {
    return request.put(`/activity/${activityId}`, data)
  },
  
  updateStatus(activityId, newStatus) {
    return request.patch(`/activity/${activityId}/status`, null, { 
      params: { new_status: newStatus } 
    })
  },
  
  delete(activityId) {
    return request.delete(`/activity/${activityId}`)
  },
  
  syncStatuses() {
    return request.post('/activity/sync-statuses')
  },
  
  getMyParticipations(activityId = null) {
    const params = {}
    if (activityId) params.activity_id = activityId
    return request.get('/activity/participations/my', { params })
  }
}

export const growthTasksApi = {
  getMyTasks() {
    return request.get('/growth-tasks/tasks')
  },
  
  getPopupStatus() {
    return request.get('/growth-tasks/popup-status')
  },
  
  markPopupSeen(isDismissed = false) {
    return request.post('/growth-tasks/popup-mark-seen', null, { 
      params: { is_dismissed: isDismissed } 
    })
  },
  
  claimReward(taskId) {
    return request.post(`/growth-tasks/claim-reward/${taskId}`)
  },
  
  triggerTask(taskType, data = {}) {
    return request.post('/growth-tasks/trigger-task', null, { 
      params: { task_type: taskType, ...data } 
    })
  }
}

export const leaderboardApi = {
  getConfigs() {
    return request.get('/leaderboards/configs')
  },
  
  getBoard(boardKey, cycleKey = null, limit = 20) {
    const params = { limit }
    if (cycleKey) params.cycle_key = cycleKey
    return request.get(`/leaderboards/board/${boardKey}`, { params })
  },
  
  getMyRank(boardKey, cycleKey = null) {
    const params = {}
    if (cycleKey) params.cycle_key = cycleKey
    return request.get(`/leaderboards/my-rank/${boardKey}`, { params })
  },
  
  getMyBadges(includeExpired = false) {
    return request.get('/leaderboards/my-badges', { params: { include_expired: includeExpired } })
  },
  
  getMyTitles(includeExpired = false) {
    return request.get('/leaderboards/my-titles', { params: { include_expired: includeExpired } })
  }
}

export const adFreeApi = {
  getPlans() {
    return request.get('/ad-free/plans')
  },
  
  getMyStatus() {
    return request.get('/ad-free/my-status')
  },
  
  getMySubscriptions(includeExpired = false) {
    return request.get('/ad-free/my-subscriptions', { params: { include_expired: includeExpired } })
  },
  
  subscribe(planKey) {
    return request.post('/ad-free/subscribe', null, { params: { plan_key: planKey } })
  }
}

export const dailyCPMatchApi = {
  getStatus() {
    return request.get('/daily-cp-match/status')
  },
  
  getMyMatches(page = 1, pageSize = 10) {
    return request.get('/daily-cp-match/my-matches', { params: { page, page_size: pageSize } })
  },
  
  getMatch(matchId) {
    return request.get(`/daily-cp-match/match/${matchId}`)
  },
  
  acceptMatch(matchId) {
    return request.post('/daily-cp-match/accept', { match_id: matchId })
  },
  
  rejectMatch(matchId) {
    return request.post('/daily-cp-match/reject', { match_id: matchId })
  },
  
  unlockProfile(matchId, targetUserId) {
    return request.post('/daily-cp-match/unlock-profile', {
      match_id: matchId,
      target_user_id: targetUserId
    })
  },
  
  extendSession(sessionId, extensionHours = 168) {
    return request.post('/daily-cp-match/extend-session', {
      session_id: sessionId,
      extension_hours: extensionHours
    })
  },
  
  manualMatch(matchType = 'vip_extra', targetZodiacSign = null) {
    const data = { match_type: matchType }
    if (targetZodiacSign) {
      data.target_zodiac_sign = targetZodiacSign
    }
    return request.post('/daily-cp-match/manual-match', data)
  },
  
  getPreference() {
    return request.get('/daily-cp-match/preference')
  },
  
  updatePreference(data) {
    return request.put('/daily-cp-match/preference', data)
  },
  
  getSession(sessionId) {
    return request.get(`/daily-cp-match/session/${sessionId}`)
  },
  
  getVipPrivileges() {
    return request.get('/daily-cp-match/vip-privileges')
  }
}

export const timeCapsuleApi = {
  initData() {
    return request.post('/time-capsules/init-data')
  },
  
  getSkins() {
    return request.get('/time-capsules/skins')
  },
  
  getQuota() {
    return request.get('/time-capsules/quota')
  },
  
  create(data) {
    return request.post('/time-capsules', data)
  },
  
  getList(params = {}) {
    return request.get('/time-capsules', { params })
  },
  
  getReceived(params = {}) {
    return request.get('/time-capsules/received', { params })
  },
  
  getDetail(capsuleId) {
    return request.get(`/time-capsules/${capsuleId}`)
  },
  
  update(capsuleId, data) {
    return request.put(`/time-capsules/${capsuleId}`, data)
  },
  
  delete(capsuleId) {
    return request.delete(`/time-capsules/${capsuleId}`)
  },
  
  open(capsuleId) {
    return request.post(`/time-capsules/${capsuleId}/open`)
  },
  
  getNotifications(params = {}) {
    return request.get('/time-capsules/notifications', { params })
  },
  
  markNotificationRead(notificationId) {
    return request.post(`/time-capsules/notifications/${notificationId}/read`)
  },
  
  processExpired() {
    return request.post('/time-capsules/process-expired')
  },
  
  getStats() {
    return request.get('/time-capsules/stats')
  }
}

export const pastLifeApi = {
  analyzeTheme(data) {
    return request.post('/past-life/analyze', data)
  },
  
  generateStory(data) {
    return request.post('/past-life/generate', data, {
      timeout: 120000
    })
  },
  
  generateDeepStory(data) {
    return request.post('/past-life/generate-deep', data, {
      timeout: 180000
    })
  },
  
  analyzeSynastry(data) {
    return request.post('/past-life/synastry/analyze', data)
  },
  
  generateSynastryStory(data) {
    return request.post('/past-life/synastry/generate', data, {
      timeout: 120000
    })
  },
  
  getMyRecords(params = {}) {
    return request.get('/past-life/my-records', { params })
  },
  
  getMySynastryRecords(params = {}) {
    return request.get('/past-life/my-synastry-records', { params })
  },
  
  getSingleRecordDetail(recordId) {
    return request.get(`/past-life/detail/${recordId}`)
  },
  
  getSynastryRecordDetail(recordId) {
    return request.get(`/past-life/synastry/detail/${recordId}`)
  },
  
  getThemes() {
    return request.get('/past-life/themes')
  },
  
  getRelationshipTypes() {
    return request.get('/past-life/relationship-types')
  },
  
  getSharedByCode(shareCode) {
    return request.get(`/past-life/share/${shareCode}`)
  },
  
  createOrder(data) {
    return request.post('/past-life/order/create', data)
  },
  
  getOrderStatus(orderNo) {
    return request.get(`/past-life/order/status/${orderNo}`)
  },
  
  upgradeWithOrder(data) {
    return request.post('/past-life/order/upgrade', data)
  }
}

export const socialPlazaApi = {
  getPostTypes() {
    return request.get('/social-plaza/types')
  },
  
  getPosts(params = {}) {
    return request.get('/social-plaza/posts', { params })
  },
  
  getPostDetail(postId) {
    return request.get(`/social-plaza/posts/${postId}`)
  },
  
  createPost(data) {
    return request.post('/social-plaza/posts', data)
  },
  
  deletePost(postId) {
    return request.delete(`/social-plaza/posts/${postId}`)
  },
  
  likePost(postId) {
    return request.post(`/social-plaza/posts/${postId}/like`)
  },
  
  getPostLikes(postId, params = {}) {
    return request.get(`/social-plaza/posts/${postId}/likes`, { params })
  },
  
  sendFlower(postId, data) {
    return request.post(`/social-plaza/posts/${postId}/flower`, data)
  },
  
  getPostFlowers(postId, params = {}) {
    return request.get(`/social-plaza/posts/${postId}/flowers`, { params })
  },
  
  createMention(postId, data) {
    return request.post(`/social-plaza/posts/${postId}/mention`, data)
  },
  
  getPostMentions(postId, params = {}) {
    return request.get(`/social-plaza/posts/${postId}/mentions`, { params })
  },
  
  respondToMention(mentionId, data) {
    return request.put(`/social-plaza/mentions/${mentionId}/respond`, data)
  },
  
  reportPost(postId, data) {
    return request.post(`/social-plaza/posts/${postId}/report`, data)
  },
  
  getMyPosts(params = {}) {
    return request.get('/social-plaza/my/posts', { params })
  },
  
  recordShare(data) {
    return request.post('/social-plaza/share', data)
  },
  
  hidePostAdmin(postId, hideReason = null) {
    const params = {}
    if (hideReason) params.hide_reason = hideReason
    return request.put(`/social-plaza/admin/posts/${postId}/hide`, null, { params })
  },
  
  removePostAdmin(postId, hideReason = null) {
    const params = {}
    if (hideReason) params.hide_reason = hideReason
    return request.put(`/social-plaza/admin/posts/${postId}/remove`, null, { params })
  }
}

export const topicChallengeApi = {
  getActiveTopic() {
    return request.get('/topic-challenge/active')
  },
  
  getTopicList(params = {}) {
    return request.get('/topic-challenge/list', { params })
  },
  
  getTopicDetail(topicId) {
    return request.get(`/topic-challenge/${topicId}`)
  },
  
  getTopicByTag(topicTag) {
    return request.get(`/topic-challenge/tag/${encodeURIComponent(topicTag)}`)
  },
  
  getTopicPosts(topicId, params = {}) {
    return request.get(`/topic-challenge/${topicId}/posts`, { params })
  },
  
  getTopicLeaderboard(topicId, params = {}) {
    return request.get(`/topic-challenge/${topicId}/leaderboard`, { params })
  },
  
  participateTopic(topicId, postId) {
    return request.post(`/topic-challenge/${topicId}/participate`, { post_id: postId })
  },
  
  claimReward(topicId) {
    return request.post(`/topic-challenge/${topicId}/claim-reward`)
  },
  
  createTopic(data) {
    return request.post('/topic-challenge/', data)
  },
  
  updateTopic(topicId, data) {
    return request.put(`/topic-challenge/${topicId}`, data)
  },
  
  settleRewards(topicId) {
    return request.post(`/topic-challenge/${topicId}/settle`)
  }
}

export const storyCardApi = {
  generate(data) {
    return request.post('/story-card/generate', data)
  },
  
  save(data) {
    return request.post('/story-card/save', data)
  },
  
  toggleMount(storyCardId, mounted = true) {
    return request.post('/story-card/mount', { story_card_id: storyCardId, mounted })
  },
  
  getMyCards(params = {}) {
    return request.get('/story-card/my-cards', { params })
  },
  
  getMyStoryWall() {
    return request.get('/story-card/story-wall')
  },
  
  getUserStoryWall(userId) {
    return request.get(`/story-card/story-wall/${userId}`)
  },
  
  getDetail(storyCardId) {
    return request.get(`/story-card/${storyCardId}`)
  },
  
  update(storyCardId, data) {
    return request.put(`/story-card/${storyCardId}`, data)
  },
  
  share(storyCardId) {
    return request.post(`/story-card/${storyCardId}/share`)
  },
  
  getByShareCode(shareCode) {
    return request.get(`/story-card/share/${shareCode}`)
  },
  
  delete(storyCardId) {
    return request.delete(`/story-card/${storyCardId}`)
  },
  
  getTemplates() {
    return request.get('/story-card/templates/list')
  },
  
  getRarityConfig() {
    return request.get('/story-card/rarity/config')
  }
}

export default request
