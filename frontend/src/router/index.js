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
        path: 'star-resonance',
        name: 'StarResonancePool',
        component: () => import('@/views/StarResonancePool.vue'),
        meta: { title: '星能共鸣池' }
      },
      {
        path: 'prediction',
        name: 'PredictionHall',
        component: () => import('@/views/PredictionHall.vue'),
        meta: { title: '预言家礼堂' }
      },
      {
        path: 'prediction/detail/:id',
        name: 'PredictionDetail',
        component: () => import('@/views/PredictionDetail.vue'),
        meta: { title: '投票详情' }
      },
      {
        path: 'prediction/result/:id',
        name: 'PredictionResult',
        component: () => import('@/views/PredictionResult.vue'),
        meta: { title: '结果公示' }
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
      },
      {
        path: 'social-icebreaker',
        name: 'SocialIcebreaker',
        component: () => import('@/views/SocialIcebreaker.vue'),
        meta: { title: '社交破冰助手' }
      },
      {
        path: 'group-matrix',
        name: 'GroupMatrix',
        component: () => import('@/views/GroupMatrix.vue'),
        meta: { title: '多人星盘关系矩阵' }
      },
      {
        path: 'life-script',
        name: 'LifeScript',
        component: () => import('@/views/LifeScript.vue'),
        meta: { title: '人生剧本时空穿梭机' }
      },
      {
        path: 'workbench',
        name: 'AstrologerWorkbench',
        component: () => import('@/views/AstrologerWorkbench.vue'),
        meta: { title: '占星师 AI 助手工作台' }
      },

      {
        path: 'plaza',
        name: 'ParallelPlaza',
        component: () => import('@/views/ParallelPlaza.vue'),
        meta: { title: '平行人生广场' }
      },
      {
        path: 'social-plaza',
        name: 'SocialPlaza',
        component: () => import('@/views/SocialPlaza.vue'),
        meta: { title: '星光广场' }
      },
      {
        path: 'topic-challenge',
        name: 'TopicChallenge',
        component: () => import('@/views/TopicChallenge.vue'),
        meta: { title: '话题挑战' }
      },
      {
        path: 'boss-hall',
        name: 'BossBattleHall',
        component: () => import('@/views/BossBattleHall.vue'),
        meta: { title: '星象BOSS副本大厅' }
      },
      {
        path: 'element-quest',
        name: 'ElementQuest',
        component: () => import('@/views/ElementQuest.vue'),
        meta: { title: '元素缺角寻宝', requiresAuth: true }
      },
      {
        path: 'phase-connect',
        name: 'PhaseConnect',
        component: () => import('@/views/PhaseConnect.vue'),
        meta: { title: '相位连连看', requiresAuth: true }
      },
      {
        path: 'network-chain',
        name: 'NetworkChain',
        component: () => import('@/views/NetworkChain.vue'),
        meta: { title: '星盘人脉链', requiresAuth: true }
      },
      {
        path: 'private-chat',
        name: 'PrivateChat',
        component: () => import('@/views/PrivateChat.vue'),
        meta: { title: '私聊消息', requiresAuth: true }
      },
      {
        path: 'vip-center',
        name: 'VIPCenter',
        component: () => import('@/views/VIPCenter.vue'),
        meta: { title: '星钻会员中心', requiresAuth: true }
      },
      {
        path: 'gift-shop',
        name: 'GiftShop',
        component: () => import('@/views/GiftShop.vue'),
        meta: { title: '礼物商城', requiresAuth: true }
      },
      {
        path: 'report-shop',
        name: 'ReportShop',
        component: () => import('@/views/ReportShop.vue'),
        meta: { title: '星盘报告商城', requiresAuth: true }
      },
      {
        path: 'invite',
        name: 'Invite',
        component: () => import('@/views/Invite.vue'),
        meta: { title: '邀请好友', requiresAuth: true }
      },
      {
        path: 'leaderboards',
        name: 'Leaderboards',
        component: () => import('@/views/Leaderboards.vue'),
        meta: { title: '荣誉排行榜' }
      },
      {
        path: 'daily-cp-match',
        name: 'DailyCPMatch',
        component: () => import('@/views/DailyCPMatch.vue'),
        meta: { title: '每日CP匹配', requiresAuth: true }
      },
      {
        path: 'time-capsule',
        name: 'TimeCapsule',
        component: () => import('@/views/TimeCapsule.vue'),
        meta: { title: '时间胶囊', requiresAuth: true }
      },
      {
        path: 'time-capsule/create',
        name: 'TimeCapsuleCreate',
        component: () => import('@/views/TimeCapsule.vue'),
        meta: { title: '创建时间胶囊', requiresAuth: true }
      },
      {
        path: 'time-capsule/edit/:id',
        name: 'TimeCapsuleEdit',
        component: () => import('@/views/TimeCapsule.vue'),
        meta: { title: '编辑时间胶囊', requiresAuth: true }
      },
      {
        path: 'time-capsule/detail/:id',
        name: 'TimeCapsuleDetail',
        component: () => import('@/views/TimeCapsuleDetail.vue'),
        meta: { title: '时间胶囊详情', requiresAuth: true }
      },
      {
        path: 'past-life',
        name: 'PastLife',
        component: () => import('@/views/PastLife.vue'),
        meta: { title: '前世故事' }
      },
      {
        path: 'past-life/records',
        name: 'PastLifeRecords',
        component: () => import('@/views/PastLifeRecords.vue'),
        meta: { title: '我的前世记录', requiresAuth: true }
      },
      {
        path: 'past-life/detail/:id',
        name: 'PastLifeDetail',
        component: () => import('@/views/PastLifeDetail.vue'),
        meta: { title: '前世故事详情' }
      },
      {
        path: 'past-life/synastry/detail/:id',
        name: 'PastLifeSynastryDetail',
        component: () => import('@/views/PastLifeDetail.vue'),
        meta: { title: '合盘前世故事详情' }
      },
      {
        path: 'past-life/share/:code',
        name: 'PastLifeShare',
        component: () => import('@/views/PastLifeShare.vue'),
        meta: { title: '前世故事分享' }
      },
      {
        path: 'story-wall',
        name: 'StoryWall',
        component: () => import('@/views/StoryWall.vue'),
        meta: { title: '我的故事墙', requiresAuth: true }
      },
      {
        path: 'story-wall/:userId',
        name: 'UserStoryWall',
        component: () => import('@/views/StoryWall.vue'),
        meta: { title: '用户故事墙' }
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
        path: 'topic-challenge',
        name: 'TopicChallengeAdmin',
        component: () => import('@/views/TopicChallengeAdmin.vue'),
        meta: { title: '话题挑战管理' }
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
