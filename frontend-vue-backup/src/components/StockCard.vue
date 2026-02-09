<script setup>
import { computed } from 'vue'

const props = defineProps({
  holding: {
    type: Object,
    required: true
  }
})

const formatCurrency = (value, currency = 'USD') => {
  if (value === undefined || value === null) return '--'
  const symbol = currency === 'CNY' ? '¥' : currency === 'HKD' ? 'HK$' : '$'
  return `${symbol}${Number(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

const formatNumber = (num) => {
  if (num === undefined || num === null) return '--'
  return Number(num).toLocaleString('en-US', { maximumFractionDigits: 0 })
}

const isProfit = computed(() => props.holding.pnl >= 0)
const isPriceUp = computed(() => props.holding.price_change_pct >= 0)

const marketIcon = computed(() => {
  switch (props.holding.market) {
    case 'CN': return '🇨🇳'
    case 'HK': return '🇭🇰'
    default: return '🇺🇸'
  }
})
</script>

<template>
  <div class="bg-slate-800 rounded-xl p-4 border border-slate-700 hover:border-slate-600 transition">
    <!-- Header -->
    <div class="flex items-start justify-between mb-3">
      <div class="flex items-center gap-2">
        <span class="text-lg">{{ marketIcon }}</span>
        <div>
          <h3 class="font-bold text-white text-lg">{{ holding.symbol }}</h3>
          <p class="text-xs text-slate-400">{{ holding.name }}</p>
        </div>
      </div>
      <div class="text-right">
        <p class="text-lg font-bold text-white">{{ formatCurrency(holding.current_price, holding.currency) }}</p>
        <p 
          class="text-sm font-medium"
          :class="isPriceUp ? 'text-green-400' : 'text-red-400'"
        >
          {{ isPriceUp ? '+' : '' }}{{ holding.price_change_pct }}%
        </p>
      </div>
    </div>

    <!-- Holdings Info -->
    <div class="grid grid-cols-2 gap-3 mb-3 py-3 border-y border-slate-700">
      <div>
        <p class="text-xs text-slate-500">持仓数量</p>
        <p class="text-sm text-white font-medium">{{ formatNumber(holding.shares) }} 股</p>
      </div>
      <div>
        <p class="text-xs text-slate-500">成本价</p>
        <p class="text-sm text-white font-medium">{{ formatCurrency(holding.avg_cost, holding.currency) }}</p>
      </div>
      <div>
        <p class="text-xs text-slate-500">成本总额</p>
        <p class="text-sm text-white font-medium">{{ formatCurrency(holding.cost_basis, holding.currency) }}</p>
      </div>
      <div>
        <p class="text-xs text-slate-500">市值</p>
        <p class="text-sm text-white font-medium">{{ formatCurrency(holding.market_value, holding.currency) }}</p>
      </div>
    </div>

    <!-- PnL -->
    <div class="flex items-center justify-between">
      <span class="text-xs text-slate-500">盈亏</span>
      <div class="text-right">
        <p 
          class="font-bold"
          :class="isProfit ? 'text-green-400' : 'text-red-400'"
        >
          {{ isProfit ? '+' : '' }}{{ formatCurrency(holding.pnl, holding.currency) }}
        </p>
        <p 
          class="text-xs"
          :class="isProfit ? 'text-green-500' : 'text-red-500'"
        >
          {{ isProfit ? '+' : '' }}{{ holding.pnl_pct }}%
        </p>
      </div>
    </div>
  </div>
</template>