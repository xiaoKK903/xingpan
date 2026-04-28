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

export default request
