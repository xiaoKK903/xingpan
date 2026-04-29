import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/',
    name: 'PublicLayout',
    component: () => import('@/views/PublicLayout.vue'),
    redirect: '/astro',
    meta: { requiresAuth: false },
    children: [
      {
        path: 'astro',
        name: 'Astro',
        component: () => import('@/views/Astro.vue'),
        meta: { title: '星盘查询' }
      },
      {
        path: 'synastry',
        name: 'Synastry',
        component: () => import('@/views/SynastryAnalysis.vue'),
        meta: { title: '双人合盘' }
      },
      {
        path: 'synastry/records',
        name: 'SynastryRecords',
        component: () => import('@/views/SynastryRecords.vue'),
        meta: { title: '合盘记录', requiresAuth: true }
      },
      {
        path: 'synastry/:id',
        name: 'SynastryDetail',
        component: () => import('@/views/SynastryAnalysis.vue'),
        meta: { title: '合盘详情', requiresAuth: true }
      },
      {
        path: 'synastry/share/:code',
        name: 'SynastryShare',
        component: () => import('@/views/SynastryAnalysis.vue'),
        meta: { title: '合盘分享' }
      },
      {
        path: 'horoscope',
        name: 'Horoscope',
        component: () => import('@/views/DailyHoroscope.vue'),
        meta: { title: '每日星运' }
      },
      {
        path: 'transit',
        name: 'TransitWeather',
        component: () => import('@/views/TransitWeather.vue'),
        meta: { title: '星象气象站' }
      },
      {
        path: 'login',
        name: 'Login',
        component: () => import('@/views/Login.vue'),
        meta: { title: '登录', hideAuth: true }
      },
      {
        path: 'register',
        name: 'Register',
        component: () => import('@/views/Register.vue'),
        meta: { title: '注册', hideAuth: true }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/Profile.vue'),
        meta: { title: '个人中心', requiresAuth: true }
      },
      {
        path: 'my-charts',
        name: 'MyCharts',
        component: () => import('@/views/MyCharts.vue'),
        meta: { title: '我的星盘', requiresAuth: true }
      }
    ]
  },
  {
    path: '/admin',
    name: 'AdminLayout',
    component: () => import('@/views/AdminLayout.vue'),
    redirect: '/admin/chat',
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('@/views/Chat.vue'),
        meta: { title: '智能客服' }
      },
      {
        path: 'conversations',
        name: 'Conversations',
        component: () => import('@/views/Conversations.vue'),
        meta: { title: '会话列表' }
      },
      {
        path: 'users',
        name: 'UserManage',
        component: () => import('@/views/UserManage.vue'),
        meta: { title: '用户管理' }
      },
      {
        path: 'profile',
        name: 'AdminProfile',
        component: () => import('@/views/Profile.vue'),
        meta: { title: '个人中心' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  document.title = to.meta.title ? `${to.meta.title} - AI智能客服` : 'AI智能客服系统'
  
  const requiresAuth = to.meta.requiresAuth || to.matched.some(record => record.meta.requiresAuth)
  const requiresAdmin = to.meta.requiresAdmin || to.matched.some(record => record.meta.requiresAdmin)
  
  if (requiresAdmin) {
    if (!userStore.isLoggedIn && !localStorage.getItem('token')) {
      next({ name: 'Login', query: { redirect: to.fullPath } })
      return
    }
    if (!userStore.isLoggedIn && localStorage.getItem('token')) {
      try {
        await userStore.getCurrentUser()
      } catch (error) {
        localStorage.removeItem('token')
        next({ name: 'Login', query: { redirect: to.fullPath } })
        return
      }
    }
    if (!userStore.isAdmin) {
      next({ name: 'Astro' })
      return
    }
  }
  else if (requiresAuth) {
    if (!userStore.isLoggedIn && !localStorage.getItem('token')) {
      next({ name: 'Login', query: { redirect: to.fullPath } })
      return
    }
    if (!userStore.isLoggedIn && localStorage.getItem('token')) {
      try {
        await userStore.getCurrentUser()
      } catch (error) {
        localStorage.removeItem('token')
        next({ name: 'Login', query: { redirect: to.fullPath } })
        return
      }
    }
  }
  
  next()
})

export default router
