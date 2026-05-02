<template>
  <div class="gift-shop-page">
    <div class="page-header">
      <h1 class="page-title">礼物商城</h1>
      <p class="page-subtitle">挑选精美礼物，表达心意</p>
    </div>

    <div class="shop-content">
      <GiftShop />
    </div>
  </div>
</template>

<script setup>
import GiftShop from '@/components/GiftShop.vue'
</script>

<style lang="scss" scoped>
.gift-shop-page {
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
  background: linear-gradient(135deg, #a78bfa, #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.page-subtitle {
  margin: 0;
  font-size: 0.95rem;
  color: rgba(255, 255, 255, 0.5);
}

@media (max-width: 768px) {
  .gift-shop-page {
    padding: 16px;
  }
}
</style>