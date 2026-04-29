<template>
  <div class="public-layout">
    <el-header class="public-header">
      <div class="header-glow"></div>
      <div class="header-inner">
        <div class="header-left">
          <router-link to="/astro" class="logo-link">
            <div class="logo-icon">
              <el-icon size="28"><Star /></el-icon>
            </div>
            <span class="logo-text">星盘查询系统</span>
          </router-link>
          <div class="nav-links">
            <router-link 
              to="/astro" 
              class="nav-link"
              :class="{ active: route.path === '/astro' }"
            >
              单人星盘
            </router-link>
            <router-link 
              to="/synastry" 
              class="nav-link"
              :class="{ active: route.path === '/synastry' }"
            >
              双人合盘
            </router-link>
            <router-link 
              to="/horoscope" 
              class="nav-link"
              :class="{ active: route.path === '/horoscope' }"
            >
              每日星运
            </router-link>
            <router-link 
              to="/transit" 
              class="nav-link"
              :class="{ active: route.path === '/transit' }"
            >
              星象气象
            </router-link>
          </div>
        </div>
        <div class="header-right">
          <template v-if="!userStore.isLoggedIn">
            <button class="nav-btn nav-btn-link" @click="goToLogin">登录</button>
            <button class="nav-btn nav-btn-primary" @click="goToRegister">注册</button>
          </template>
          <template v-else-if="userStore.isAdmin">
            <button class="nav-btn nav-btn-primary" @click="goToAdmin">
              <el-icon><User /></el-icon>
              管理后台
            </button>
            <el-dropdown @command="handleCommand">
              <span class="user-info">
                <div class="user-avatar">
                  <el-icon><UserFilled /></el-icon>
                </div>
                <span class="username">{{ userStore.username }}</span>
                <el-icon class="arrow-icon"><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu class="custom-dropdown-menu">
                  <el-dropdown-item command="admin">后台管理</el-dropdown-item>
                  <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                  <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
          <template v-else>
            <button class="nav-btn nav-btn-link" @click="goToMyCharts">
              <el-icon><Star /></el-icon>
              我的星盘
            </button>
            <button class="nav-btn nav-btn-primary" @click="goToProfile">
              <el-icon><User /></el-icon>
              个人中心
            </button>
            <el-dropdown @command="handleCommand">
              <span class="user-info">
                <div class="user-avatar">
                  <el-icon><UserFilled /></el-icon>
                </div>
                <span class="username">{{ userStore.username }}</span>
                <el-icon class="arrow-icon"><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu class="custom-dropdown-menu">
                  <el-dropdown-item command="charts">我的星盘</el-dropdown-item>
                  <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                  <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </div>
      </div>
    </el-header>
    <el-main class="public-main">
      <router-view />
    </el-main>
  </div>
</template>

<script setup>
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { computed } from 'vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const showAuthButtons = computed(() => !route.meta.hideAuth)

function goToLogin() {
  router.push('/login')
}

function goToRegister() {
  router.push('/register')
}

function goToAdmin() {
  router.push('/admin/chat')
}

function goToMyCharts() {
  router.push('/my-charts')
}

function goToProfile() {
  router.push('/profile')
}

function handleCommand(command) {
  switch (command) {
    case 'admin':
      router.push('/admin/chat')
      break
    case 'charts':
      router.push('/my-charts')
      break
    case 'profile':
      router.push('/profile')
      break
    case 'logout':
      userStore.logout()
      break
  }
}
</script>

<style lang="scss" scoped>
.public-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.public-header {
  height: 64px;
  position: relative;
  z-index: 100;
  flex-shrink: 0;
}

.header-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(12, 12, 35, 0.35);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(139, 92, 246, 0.12);
}

.header-inner {
  position: relative;
  z-index: 1;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 40px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 24px;
  
  .logo-link {
    display: flex;
    align-items: center;
    gap: 12px;
    text-decoration: none;
    
    .logo-icon {
      width: 44px;
      height: 44px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: radial-gradient(circle, rgba(139, 92, 246, 0.3) 0%, transparent 70%);
      border-radius: 12px;
      color: #a78bfa;
      transition: all 0.3s ease;
    }
    
    &:hover .logo-icon {
      transform: scale(1.1);
      box-shadow: 0 0 30px rgba(139, 92, 246, 0.4);
    }
    
    .logo-text {
      font-size: 18px;
      font-weight: 600;
      background: linear-gradient(135deg, #a78bfa 0%, #60a5fa 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
  }
  
  .nav-links {
    display: flex;
    align-items: center;
    gap: 8px;
    padding-left: 24px;
    border-left: 1px solid rgba(139, 92, 246, 0.2);
  }
  
  .nav-link {
    padding: 8px 16px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.6);
    text-decoration: none;
    transition: all 0.2s ease;
    
    &:hover {
      background: rgba(139, 92, 246, 0.15);
      color: rgba(255, 255, 255, 0.9);
    }
    
    &.active {
      background: rgba(139, 92, 246, 0.25);
      color: #c4b5fd;
    }
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-btn {
  padding: 10px 20px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  
  &:hover {
    transform: translateY(-1px);
  }
}

.nav-btn-link {
  background: transparent;
  color: rgba(255, 255, 255, 0.8);
  
  &:hover {
    background: rgba(139, 92, 246, 0.15);
    color: #c4b5fd;
  }
}

.nav-btn-primary {
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  color: #fff;
  box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
  
  &:hover {
    box-shadow: 0 6px 25px rgba(139, 92, 246, 0.4);
  }
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.15);
  }
  
  .user-avatar {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
    border-radius: 50%;
    color: #fff;
    font-size: 14px;
  }
  
  .username {
    color: rgba(255, 255, 255, 0.9);
    font-size: 14px;
    font-weight: 500;
  }
  
  .arrow-icon {
    color: rgba(255, 255, 255, 0.5);
    font-size: 12px;
    transition: transform 0.3s ease;
  }
}

:deep(.el-dropdown-menu__item) {
  &.el-dropdown-menu__item--divided {
    border-top-color: rgba(139, 92, 246, 0.2);
  }
}

.public-main {
  flex: 1;
  padding: 0;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;
}
</style>
