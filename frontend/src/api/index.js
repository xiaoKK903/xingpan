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
      return data.data || data
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
        default:
          ElMessage.error(error.response.data?.detail || error.message || '请求失败')
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
  
  register(username, password, email) {
    return request.post('/users/register', {
      username,
      password,
      email
    })
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

export default request
