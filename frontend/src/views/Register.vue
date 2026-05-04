<template>
  <div class="register-container">
    <div class="stars-bg">
      <div v-for="i in 60" :key="i" class="star" :style="getStarStyle(i)"></div>
    </div>
    
    <div class="glow-orbs">
      <div class="glow-orb orb-1"></div>
      <div class="glow-orb orb-2"></div>
    </div>

    <div class="register-main">
      <div class="register-header">
        <div class="header-icon">
          <el-icon size="36"><Star /></el-icon>
        </div>
        <h1 class="main-title">创建账户</h1>
        <p class="subtitle">加入我们，开启你的星盘探索之旅</p>
      </div>

      <div class="register-card-wrapper">
        <div class="register-card">
          <div class="card-border-glow"></div>
          <div class="card-glow"></div>
          
          <div class="card-content">
            <form class="register-form">
              <div class="form-group">
                <label class="form-label">
                  <span class="label-icon"><el-icon><User /></el-icon></span>
                  <span>用户名</span>
                </label>
                <div class="input-wrapper">
                  <input 
                    type="text" 
                    v-model="registerForm.username" 
                    placeholder="请输入用户名（2-50个字符）"
                    class="astro-input"
                  />
                  <div class="input-border-effect"></div>
                </div>
              </div>

              <div class="form-group">
                <label class="form-label">
                  <span class="label-icon"><el-icon><Message /></el-icon></span>
                  <span>邮箱（选填）</span>
                </label>
                <div class="input-wrapper">
                  <input 
                    type="email" 
                    v-model="registerForm.email" 
                    placeholder="请输入邮箱地址"
                    class="astro-input"
                  />
                  <div class="input-border-effect"></div>
                </div>
              </div>

              <div class="form-group">
                <label class="form-label">
                  <span class="label-icon"><el-icon><Lock /></el-icon></span>
                  <span>密码</span>
                </label>
                <div class="input-wrapper">
                  <input 
                    :type="showPassword ? 'text' : 'password'"
                    v-model="registerForm.password" 
                    placeholder="请输入密码（至少6个字符）"
                    class="astro-input"
                  />
                  <button 
                    type="button" 
                    class="password-toggle"
                    @click="showPassword = !showPassword"
                  >
                    <el-icon><View v-if="!showPassword" /><Hide v-else /></el-icon>
                  </button>
                  <div class="input-border-effect"></div>
                </div>
              </div>

              <div class="form-group">
                <label class="form-label">
                  <span class="label-icon"><el-icon><Lock /></el-icon></span>
                  <span>确认密码</span>
                </label>
                <div class="input-wrapper">
                  <input 
                    :type="showConfirmPassword ? 'text' : 'password'"
                    v-model="registerForm.confirmPassword" 
                    placeholder="请再次输入密码"
                    class="astro-input"
                    @keyup.enter="handleRegister"
                  />
                  <button 
                    type="button" 
                    class="password-toggle"
                    @click="showConfirmPassword = !showConfirmPassword"
                  >
                    <el-icon><View v-if="!showConfirmPassword" /><Hide v-else /></el-icon>
                  </button>
                  <div class="input-border-effect"></div>
                </div>
              </div>

              <div class="form-group">
                <label class="form-label">
                  <span class="label-icon"><el-icon><Share /></el-icon></span>
                  <span>邀请码（可选）</span>
                </label>
                <div class="input-wrapper invite-code-wrapper">
                  <input 
                    type="text"
                    v-model="registerForm.inviteCode" 
                    placeholder="请输入邀请码"
                    class="astro-input invite-code-input"
                    @blur="validateInviteCode"
                  />
                  <button 
                    v-if="registerForm.inviteCode && !inviteCodeValid"
                    type="button" 
                    class="validate-btn"
                    @click="validateInviteCode"
                    :disabled="validatingCode"
                  >
                    <span v-if="validatingCode">验证中...</span>
                    <span v-else>验证</span>
                  </button>
                  <div v-if="inviteCodeValid" class="valid-icon">
                    <el-icon color="#22c55e"><Check /></el-icon>
                  </div>
                  <div class="input-border-effect"></div>
                </div>
                <div v-if="inviterInfo" class="inviter-info">
                  <span class="inviter-label">邀请人：</span>
                  <span class="inviter-name">{{ inviterInfo.username }}</span>
                  <el-tag size="small" type="success">双方各得50星元碎片</el-tag>
                </div>
              </div>

              <div class="submit-section">
                <button 
                  type="button" 
                  class="submit-btn"
                  :class="{ 'btn-loading': loading }"
                  @click="handleRegister"
                >
                  <span class="btn-content">
                    <span class="btn-spinner" v-if="loading"></span>
                    <span>{{ loading ? '注册中...' : '立即注册' }}</span>
                  </span>
                  <div class="btn-glow"></div>
                </button>
              </div>
            </form>

            <div class="divider-wrapper">
              <div class="divider-line"></div>
            </div>

            <div class="login-link">
              <span>已有账户？</span>
              <router-link to="/login" class="link-btn">立即登录</router-link>
            </div>

            <div class="back-link">
              <router-link to="/astro" class="back-btn">
                <el-icon><ArrowLeft /></el-icon>
                返回首页
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { userApi, inviteApi } from '@/api'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const validatingCode = ref(false)
const inviteCodeValid = ref(false)
const inviterInfo = ref(null)

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  inviteCode: ''
})

function getStarStyle(index) {
  const size = Math.random() * 2 + 1
  return {
    left: `${Math.random() * 100}%`,
    top: `${Math.random() * 100}%`,
    width: `${size}px`,
    height: `${size}px`,
    animationDelay: `${Math.random() * 4}s`,
    opacity: Math.random() * 0.4 + 0.2
  }
}

async function validateInviteCode() {
  if (!registerForm.inviteCode) {
    inviteCodeValid.value = false
    inviterInfo.value = null
    return
  }
  
  validatingCode.value = true
  try {
    const result = await inviteApi.validateCode(registerForm.inviteCode)
    inviteCodeValid.value = result.valid
    if (result.valid) {
      inviterInfo.value = result.inviter
      ElMessage.success({
        message: `邀请码有效，邀请人：${result.inviter?.username || '神秘星友'}`,
        duration: 2000
      })
    } else {
      inviterInfo.value = null
      ElMessage.warning('邀请码无效或已过期')
    }
  } catch (error) {
    inviteCodeValid.value = false
    inviterInfo.value = null
    console.error('验证邀请码失败:', error)
  } finally {
    validatingCode.value = false
  }
}

async function handleRegister() {
  if (!registerForm.username || !registerForm.password) {
    return
  }
  
  if (registerForm.password !== registerForm.confirmPassword) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  
  if (registerForm.username.length < 2 || registerForm.username.length > 50) {
    ElMessage.warning('用户名长度为 2-50 个字符')
    return
  }
  
  if (registerForm.password.length < 6) {
    ElMessage.warning('密码至少 6 个字符')
    return
  }
  
  loading.value = true
  try {
    await userApi.register(
      registerForm.username,
      registerForm.password,
      registerForm.email || undefined,
      registerForm.inviteCode || undefined
    )
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch (error) {
    console.error('注册失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  const codeFromQuery = route.query.invite_code || route.query.inviteCode
  if (codeFromQuery) {
    registerForm.inviteCode = codeFromQuery
    validateInviteCode()
  }
})
</script>

<style lang="scss" scoped>
.register-container {
  height: 100vh;
  width: 100%;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #0a0a1a 0%, #1a1a3e 50%, #0f0f2a 100%);
}

.stars-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.star {
  position: absolute;
  background: #fff;
  border-radius: 50%;
  animation: twinkle 4s ease-in-out infinite;
}

@keyframes twinkle {
  0%, 100% { opacity: 0.2; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.3); }
}

.glow-orbs {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
  overflow: hidden;
}

.glow-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.35;
}

.orb-1 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, #8b5cf6 0%, transparent 70%);
  top: -200px;
  right: -100px;
  animation: float-1 25s ease-in-out infinite;
}

.orb-2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, #3b82f6 0%, transparent 70%);
  bottom: -100px;
  left: -100px;
  animation: float-2 20s ease-in-out infinite;
}

@keyframes float-1 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-80px, 50px); }
}

@keyframes float-2 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(60px, -40px); }
}

.register-main {
  position: relative;
  z-index: 10;
  flex: 1;
  padding: 20px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  box-sizing: border-box;
  overflow-y: auto;
}

.register-header {
  text-align: center;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.header-icon {
  width: 56px;
  height: 56px;
  margin: 0 auto 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.3) 0%, transparent 70%);
  border-radius: 50%;
  color: #a78bfa;
  animation: pulse-glow 4s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 20px rgba(139, 92, 246, 0.25); }
  50% { box-shadow: 0 0 40px rgba(139, 92, 246, 0.4); }
}

.main-title {
  font-size: 1.8rem;
  font-weight: 700;
  background: linear-gradient(135deg, #a78bfa 0%, #60a5fa 50%, #34d399 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 6px 0;
  text-shadow: 0 0 30px rgba(139, 92, 246, 0.4);
}

.subtitle {
  color: rgba(255, 255, 255, 0.55);
  font-size: 0.85rem;
  margin: 0;
  font-weight: 300;
}

.register-card-wrapper {
  flex-shrink: 0;
  width: 100%;
  max-width: 420px;
}

.register-card {
  position: relative;
  background: rgba(18, 18, 40, 0.7);
  backdrop-filter: blur(25px);
  -webkit-backdrop-filter: blur(25px);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 
    0 0 30px rgba(139, 92, 246, 0.08),
    0 0 60px rgba(139, 92, 246, 0.04),
    0 8px 32px rgba(0, 0, 0, 0.25);
}

.card-border-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border: 1px solid transparent;
  border-radius: 20px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.4), rgba(99, 102, 241, 0.2), rgba(59, 130, 246, 0.3)) border-box;
  -webkit-mask:
    linear-gradient(#fff 0 0) padding-box,
    linear-gradient(#fff 0 0);
  mask:
    linear-gradient(#fff 0 0) padding-box,
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
  z-index: 2;
}

.card-glow {
  position: absolute;
  top: -30%;
  left: -30%;
  width: 160%;
  height: 160%;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.08) 0%, transparent 60%);
  pointer-events: none;
  z-index: 1;
}

.card-content {
  position: relative;
  z-index: 10;
  padding: 24px 28px;
}

.register-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 6px;
  color: rgba(255, 255, 255, 0.85);
  font-size: 0.85rem;
  font-weight: 500;
}

.label-icon {
  color: #a78bfa;
  display: flex;
  align-items: center;
  font-size: 0.9rem;
}

.input-wrapper {
  position: relative;
}

.astro-input {
  width: 100%;
  padding: 12px 40px 12px 16px;
  background: rgba(30, 30, 60, 0.5);
  border: 1px solid rgba(139, 92, 246, 0.25);
  border-radius: 10px;
  color: #fff;
  font-size: 0.9rem;
  transition: all 0.3s ease;
  outline: none;
  box-sizing: border-box;
  
  &::placeholder {
    color: rgba(255, 255, 255, 0.35);
  }
  
  &:focus {
    border-color: rgba(139, 92, 246, 0.7);
    box-shadow: 0 0 15px rgba(139, 92, 246, 0.2), inset 0 0 15px rgba(139, 92, 246, 0.03);
  }
  
  &:hover:not(:focus) {
    border-color: rgba(139, 92, 246, 0.4);
  }
}

.password-toggle {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  border: none;
  color: rgba(167, 139, 250, 0.6);
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.3s ease;
  
  &:hover {
    color: #a78bfa;
  }
}

.input-border-effect {
  position: absolute;
  bottom: 1px;
  left: 50%;
  width: 0;
  height: 2px;
  background: linear-gradient(90deg, #8b5cf6, #3b82f6);
  transition: all 0.3s ease;
  transform: translateX(-50%);
  border-radius: 0 0 10px 10px;
  pointer-events: none;
}

.input-wrapper:focus-within .input-border-effect {
  width: calc(100% - 2px);
}

.invite-code-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .invite-code-input {
    flex: 1;
    padding-right: 80px;
  }
  
  .validate-btn {
    position: absolute;
    right: 8px;
    top: 50%;
    transform: translateY(-50%);
    padding: 6px 12px;
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.8) 0%, rgba(99, 102, 241, 0.8) 100%);
    border: none;
    border-radius: 6px;
    color: #fff;
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.3s ease;
    
    &:hover:not(:disabled) {
      background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
    }
    
    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
  }
  
  .valid-icon {
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    display: flex;
    align-items: center;
  }
}

.inviter-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  margin-top: 8px;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.25);
  border-radius: 8px;
  
  .inviter-label {
    color: rgba(255, 255, 255, 0.6);
    font-size: 0.8rem;
  }
  
  .inviter-name {
    color: #22c55e;
    font-weight: 600;
    font-size: 0.85rem;
  }
}

.submit-section {
  margin-top: 6px;
}

.submit-btn {
  position: relative;
  width: 100%;
  padding: 14px 28px;
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 50%, #3b82f6 100%);
  border: none;
  border-radius: 12px;
  color: #fff;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 30px rgba(139, 92, 246, 0.35);
  }
  
  &:active {
    transform: translateY(0);
  }
  
  &.btn-loading {
    cursor: not-allowed;
    opacity: 0.85;
  }
}

.btn-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  position: relative;
  z-index: 2;
}

.btn-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.btn-glow {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.15), transparent);
  transition: left 0.6s ease;
  pointer-events: none;
}

.submit-btn:hover .btn-glow {
  left: 100%;
}

.divider-wrapper {
  display: flex;
  align-items: center;
  margin: 16px 0;
}

.divider-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.3), transparent);
}

.login-link {
  text-align: center;
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.85rem;
  
  .link-btn {
    color: #a78bfa;
    text-decoration: none;
    font-weight: 500;
    margin-left: 4px;
    transition: color 0.3s ease;
    
    &:hover {
      color: #c4b5fd;
      text-decoration: underline;
    }
  }
}

.back-link {
  text-align: center;
  margin-top: 12px;
  
  .back-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    color: rgba(255, 255, 255, 0.5);
    font-size: 0.8rem;
    text-decoration: none;
    transition: color 0.3s ease;
    
    &:hover {
      color: rgba(255, 255, 255, 0.7);
    }
  }
}
</style>
