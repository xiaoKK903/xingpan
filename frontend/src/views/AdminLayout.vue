<template>
  <el-container class="layout-container">
    <el-aside width="240px" class="sidebar">
      <div class="sidebar-glow"></div>
      <div class="logo">
        <div class="logo-icon">
          <el-icon size="28"><Star /></el-icon>
        </div>
        <span>管理后台</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        router
        background-color="transparent"
        text-color="rgba(255,255,255,0.7)"
        active-text-color="#a78bfa"
      >
        <el-menu-item index="/admin/chat">
          <el-icon><ChatDotRound /></el-icon>
          <span>智能客服</span>
        </el-menu-item>
        <el-menu-item index="/admin/conversations">
          <el-icon><Document /></el-icon>
          <span>会话列表</span>
        </el-menu-item>
        <el-menu-item index="/admin/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/profile">
          <el-icon><Setting /></el-icon>
          <span>个人中心</span>
        </el-menu-item>
      </el-menu>
      <div class="back-to-public">
        <button class="back-btn" @click="goToPublic">
          <el-icon><Back /></el-icon>
          <span>返回首页</span>
        </button>
      </div>
    </el-aside>
    <el-container class="main-container">
      <el-header class="header">
        <div class="header-glow"></div>
        <div class="header-inner">
          <div class="header-left">
            <el-breadcrumb separator="/">
              <el-breadcrumb-item :to="{ path: '/astro' }">
                <span class="breadcrumb-item">首页</span>
              </el-breadcrumb-item>
              <el-breadcrumb-item>
                <span class="breadcrumb-item current">{{ currentTitle }}</span>
              </el-breadcrumb-item>
            </el-breadcrumb>
          </div>
          <div class="header-right">
            <el-dropdown @command="handleCommand" trigger="click">
              <div class="user-dropdown">
                <div class="user-avatar">
                  <el-icon><UserFilled /></el-icon>
                </div>
                <div class="user-info">
                  <span class="username">{{ userStore.username }}</span>
                  <span class="user-role">管理员</span>
                </div>
                <el-icon class="arrow-icon"><ArrowDown /></el-icon>
              </div>
              <template #dropdown>
                <div class="custom-dropdown">
                  <div class="dropdown-header">
                    <div class="dropdown-avatar">
                      <el-icon size="24"><UserFilled /></el-icon>
                    </div>
                    <div class="dropdown-user-info">
                      <span class="dropdown-username">{{ userStore.username }}</span>
                      <span class="dropdown-email">{{ userStore.email || '未设置邮箱' }}</span>
                    </div>
                  </div>
                  <div class="dropdown-divider"></div>
                  <div class="dropdown-item" @click="handleCommand('profile')">
                    <el-icon><Setting /></el-icon>
                    <span>个人中心</span>
                  </div>
                  <div class="dropdown-divider"></div>
                  <div class="dropdown-item logout-item" @click="handleCommand('logout')">
                    <el-icon><SwitchButton /></el-icon>
                    <span>退出登录</span>
                  </div>
                </div>
              </template>
            </el-dropdown>
          </div>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)
const currentTitle = computed(() => route.meta.title || '')

function goToPublic() {
  router.push('/astro')
}

function handleCommand(command) {
  switch (command) {
    case 'profile':
      router.push('/admin/profile')
      break
    case 'logout':
      userStore.logout()
      break
  }
}
</script>

<style lang="scss" scoped>
.layout-container {
  height: 100%;
  background: linear-gradient(180deg, #0a0a1a 0%, #1a1a3e 50%, #0f0f2a 100%);
}

.sidebar {
  position: relative;
  background: rgba(15, 15, 35, 0.9);
  border-right: 1px solid rgba(139, 92, 246, 0.15);
  display: flex;
  flex-direction: column;
}

.sidebar-glow {
  position: absolute;
  top: 0;
  right: 0;
  width: 2px;
  height: 100%;
  background: linear-gradient(180deg, transparent, rgba(139, 92, 246, 0.3), transparent);
  pointer-events: none;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 12px;
  padding: 0 20px;
  border-bottom: 1px solid rgba(139, 92, 246, 0.15);
  
  .logo-icon {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
    border-radius: 10px;
    color: #fff;
    box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
  }
  
  span {
    font-size: 17px;
    font-weight: 600;
    background: linear-gradient(135deg, #a78bfa 0%, #60a5fa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
}

.sidebar-menu {
  border-right: none;
  flex: 1;
  padding: 12px 0;
  
  :deep(.el-menu-item) {
    height: 48px;
    line-height: 48px;
    margin: 4px 12px;
    border-radius: 10px;
    transition: all 0.3s ease;
    
    &.is-active {
      background: linear-gradient(90deg, rgba(139, 92, 246, 0.2) 0%, rgba(139, 92, 246, 0.05) 100%);
      border-left: 3px solid #8b5cf6;
      
      &::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 3px;
        background: linear-gradient(180deg, #8b5cf6 0%, #3b82f6 100%);
        border-radius: 0 3px 3px 0;
      }
    }
    
    &:hover:not(.is-active) {
      background: rgba(139, 92, 246, 0.1);
    }
  }
}

.back-to-public {
  padding: 16px 20px;
  border-top: 1px solid rgba(139, 92, 246, 0.15);
}

.back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 10px 16px;
  background: rgba(139, 92, 246, 0.1);
  border: 1px solid rgba(139, 92, 246, 0.25);
  border-radius: 10px;
  color: rgba(167, 139, 250, 0.9);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.2);
    border-color: rgba(139, 92, 246, 0.4);
    color: #c4b5fd;
  }
}

.main-container {
  display: flex;
  flex-direction: column;
}

.header {
  position: relative;
  height: 64px;
  flex-shrink: 0;
}

.header-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 15, 35, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(139, 92, 246, 0.15);
}

.header-inner {
  position: relative;
  z-index: 1;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.breadcrumb-item {
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
  transition: color 0.3s ease;
  cursor: pointer;
  
  &:hover {
    color: #a78bfa;
  }
  
  &.current {
    color: rgba(255, 255, 255, 0.9);
    font-weight: 500;
  }
}

.header-right {
  display: flex;
  align-items: center;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.1);
  }
}

.user-avatar {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  border-radius: 50%;
  color: #fff;
  flex-shrink: 0;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  
  .username {
    color: rgba(255, 255, 255, 0.9);
    font-size: 14px;
    font-weight: 500;
  }
  
  .user-role {
    color: rgba(255, 255, 255, 0.5);
    font-size: 12px;
  }
}

.arrow-icon {
  color: rgba(255, 255, 255, 0.5);
  font-size: 12px;
  transition: transform 0.3s ease;
}

.custom-dropdown {
  width: 220px;
  background: rgba(20, 20, 45, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 12px;
  border: 1px solid rgba(139, 92, 246, 0.2);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  padding: 0;
  overflow: hidden;
}

.dropdown-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
}

.dropdown-avatar {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  border-radius: 50%;
  color: #fff;
  flex-shrink: 0;
}

.dropdown-user-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  
  .dropdown-username {
    color: rgba(255, 255, 255, 0.9);
    font-size: 15px;
    font-weight: 600;
  }
  
  .dropdown-email {
    color: rgba(255, 255, 255, 0.5);
    font-size: 12px;
  }
}

.dropdown-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.2), transparent);
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(139, 92, 246, 0.15);
    color: #a78bfa;
  }
  
  &.logout-item {
    color: rgba(239, 68, 68, 0.8);
    
    &:hover {
      background: rgba(239, 68, 68, 0.1);
      color: #f87171;
    }
  }
}

.main-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background: transparent;
}
</style>
