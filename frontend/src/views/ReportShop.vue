<template>
  <div class="report-shop-page">
    <div class="page-header">
      <h1 class="page-title">星盘报告商城</h1>
      <p class="page-subtitle">深度星盘分析，洞察人生奥秘</p>
    </div>

    <div class="shop-content">
      <ReportShop
        :is-vip="isVip"
        :free-reports-remaining="freeReportsRemaining"
        :is-logged-in="isLoggedIn"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useUserStore } from '@/stores/user'
import ReportShop from '@/components/ReportShop.vue'

const userStore = useUserStore()

const isVip = computed(() => userStore.isVip)
const freeReportsRemaining = computed(() => userStore.vipFreeReportsRemaining)
const isLoggedIn = computed(() => userStore.isLoggedIn)
</script>

<style lang="scss" scoped>
.report-shop-page {
  max-width: 1000px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  text-align: center;
  margin-bottom: 24px;
}

.page-title {
  margin: 0 0 8px;
  font-size: 1.8rem;
  font-weight: 700;
  background: linear-gradient(135deg, #a78bfa, #6366f1);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.page-subtitle {
  margin: 0;
  font-size: 0.95rem;
  color: rgba(255, 255, 255, 0.5);
}

@media (max-width: 768px) {
  .report-shop-page {
    padding: 16px;
  }
}
</style>