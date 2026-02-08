import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'

const API_BASE = '/api'

export const useDashboardStore = defineStore('dashboard', () => {
  // State
  const summary = ref(null)
  const activities = ref([])
  const stockPortfolio = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const completedTasksToday = computed(() => summary.value?.trello?.completed_today || 0)
  const commitsToday = computed(() => summary.value?.github?.commits_today || 0)
  
  const totalStockPnl = computed(() => {
    if (!stockPortfolio.value?.summary) return 0
    return stockPortfolio.value.summary.total_pnl_pct || 0
  })
  
  const formattedStockPnl = computed(() => {
    const pnl = totalStockPnl.value
    return `${pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}%`
  })

  // Actions
  async function fetchSummary() {
    loading.value = true
    try {
      const { data } = await axios.get(`${API_BASE}/dashboard/summary`)
      summary.value = data
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchTimeline(period = 'today') {
    loading.value = true
    try {
      const { data } = await axios.get(`${API_BASE}/timeline/${period}`)
      activities.value = data.activities
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchStockPortfolio() {
    try {
      const { data } = await axios.get(`${API_BASE}/stocks/portfolio`)
      if (data.success) {
        stockPortfolio.value = data.data
      }
    } catch (e) {
      console.error('Failed to fetch stock portfolio:', e)
    }
  }

  return {
    summary,
    activities,
    stockPortfolio,
    loading,
    error,
    completedTasksToday,
    commitsToday,
    totalStockPnl,
    formattedStockPnl,
    fetchSummary,
    fetchTimeline,
    fetchStockPortfolio
  }
})
