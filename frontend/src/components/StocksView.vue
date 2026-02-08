<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import StockCard from './StockCard.vue'

const API_BASE = '/api'

const portfolio = ref(null)
const loading = ref(false)
const error = ref(null)
const selectedPeriod = ref('1mo')

const periods = [
  { value: '1mo', label: '1个月' },
  { value: '3mo', label: '3个月' },
  { value: '6mo', label: '6个月' },
  { value: '1y', label: '1年' }
]

const fetchPortfolio = async () => {
  loading.value = true
  error.value = null
  
  try {
    const { data } = await axios.get(`${API_BASE}/stocks/portfolio`)
    if (data.success) {
      portfolio.value = data.data
    }
  } catch (e) {
    error.value = e.response?.data?.detail || '获取股票数据失败'
  } finally {
    loading.value = false
  }
}

const fetchPerformance = async () => {
  try {
    const { data } = await axios.get(`${API_BASE}/stocks/performance?period=${selectedPeriod.value}`)
    // 可以在这里处理性能数据
  } catch (e) {
    console.error('Failed to fetch performance:', e)
  }
}

const refreshData = () => {
  fetchPortfolio()
  fetchPerformance()
}

const formatCurrency = (value, currency = 'USD') => {
  if (value === undefined || value === null) return '--'
  const symbol = currency === 'CNY' ? '¥' : currency === 'HKD' ? 'HK$' : '$'
  return `${symbol}${Number(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

const totalProfit = computed(() => {
  if (!portfolio.value) return 0
  return portfolio.value.summary.total_pnl
})

const totalProfitPct = computed(() => {
  if (!portfolio.value) return 0
  return portfolio.value.summary.total_pnl_pct
})

const isTotalProfit = computed(() => totalProfit.value >= 0)

onMounted(() => {
  fetchPortfolio()
  fetchPerformance()
})
</script>

<template>
  <div class="bg-slate-900 rounded-xl p-6 border border-slate-800">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center text-xl">
          📈
        </div>
        <div>
          <h2 class="text-xl font-bold text-white">股票持仓</h2>
          <p class="text-sm text-slate-400">实时盈亏监控</p>
        </div>
      </div>

      <div class="flex items-center gap-4">
        <!-- Period Selector -->
        <select 
          v-model="selectedPeriod"
          @change="fetchPerformance"
          class="bg-slate-800 text-white text-sm rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:border-blue-500"
        >
          <option v-for="period in periods" :key="period.value" :value="period.value">
            {{ period.label }}
          </option>
        </select>

        <!-- Refresh Button -->
        <button 
          @click="refreshData"
          :disabled="loading"
          class="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm px-4 py-2 rounded-lg transition"
        >
          {{ loading ? '刷新中...' : '刷新' }}
        </button>
      </div>
    </div>

    <!-- Summary Cards -->
    <div v-if="portfolio" class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <div class="bg-slate-800 rounded-lg p-4 border border-slate-700">
        <p class="text-sm text-slate-400">总成本</p>
        <p class="text-xl font-bold text-white">{{ formatCurrency(portfolio.summary.total_cost) }}</p>
      </div>

      <div class="bg-slate-800 rounded-lg p-4 border border-slate-700">
        <p class="text-sm text-slate-400">总市值</p>
        <p class="text-xl font-bold text-white">{{ formatCurrency(portfolio.summary.total_value) }}</p>
      </div>

      <div class="bg-slate-800 rounded-lg p-4 border border-slate-700">
        <p class="text-sm text-slate-400">总盈亏</p>
        <div class="flex items-center gap-2">
          <p 
            class="text-xl font-bold"
            :class="isTotalProfit ? 'text-green-400' : 'text-red-400'"
          >
            {{ isTotalProfit ? '+' : '' }}{{ formatCurrency(totalProfit) }}
          </p>
          <span 
            class="text-sm px-2 py-0.5 rounded"
            :class="isTotalProfit ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'"
          >
            {{ isTotalProfit ? '+' : '' }}{{ totalProfitPct }}%
          </span>
        </div>
      </div>
    </div>

    <!-- Holdings Grid -->
    <div v-if="loading" class="text-center py-12">
      <div class="inline-block w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      <p class="text-slate-400 mt-2">加载中...</p>
    </div>

    <div v-else-if="error" class="text-center py-12">
      <p class="text-red-400">{{ error }}</p>
      <button 
        @click="fetchPortfolio"
        class="mt-4 text-blue-400 hover:text-blue-300"
      >
        重试
      </button>
    </div>

    <div v-else-if="portfolio" class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <StockCard 
        v-for="holding in portfolio.holdings" 
        :key="holding.symbol"
        :holding="holding"
      />
    </div>

    <!-- Last Updated -->
    <p v-if="portfolio?.summary?.updated_at" class="text-xs text-slate-500 mt-4 text-right">
      更新时间: {{ new Date(portfolio.summary.updated_at).toLocaleString('zh-CN') }}
    </p>
  </div>
</template>