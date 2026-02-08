import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'

const API_BASE = '/api'

// 从 localStorage 获取 token，或从环境变量/配置中获取
const getApiToken = () => {
  return localStorage.getItem('dashboard_api_token') || import.meta.env.VITE_API_TOKEN || ''
}

// 配置 axios 拦截器添加 token
const setupAxiosInterceptors = () => {
  axios.interceptors.request.use((config) => {
    const token = getApiToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  })
  
  axios.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401 || error.response?.status === 403) {
        // Token 无效，清除存储
        localStorage.removeItem('dashboard_api_token')
        // 可以在这里触发登录弹窗
        console.error('API Token 无效或已过期')
      }
      return Promise.reject(error)
    }
  )
}

setupAxiosInterceptors()

export const useDashboardStore = defineStore('dashboard', () => {
  // State
  const summary = ref(null)
  const activities = ref([])
  const stockPortfolio = ref(null)
  const weatherData = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const apiToken = ref(getApiToken())

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
  
  const isAuthenticated = computed(() => !!apiToken.value)

  // Actions
  function setApiToken(token) {
    apiToken.value = token
    localStorage.setItem('dashboard_api_token', token)
  }
  
  function clearApiToken() {
    apiToken.value = ''
    localStorage.removeItem('dashboard_api_token')
  }

  async function fetchSummary() {
    loading.value = true
    error.value = null
    try {
      const { data } = await axios.get(`${API_BASE}/dashboard/summary`)
      summary.value = data
    } catch (e) {
      error.value = e.message
      console.error('Failed to fetch summary:', e)
    } finally {
      loading.value = false
    }
  }

  async function fetchTimeline(period = 'today') {
    loading.value = true
    error.value = null
    try {
      const { data } = await axios.get(`${API_BASE}/timeline/${period}`)
      activities.value = data.activities || []
    } catch (e) {
      error.value = e.message
      console.error('Failed to fetch timeline:', e)
      activities.value = []
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
  
  async function fetchWeather() {
    try {
      const { data } = await axios.get(`${API_BASE}/weather/current`)
      if (data.success) {
        weatherData.value = data.data
      }
    } catch (e) {
      console.error('Failed to fetch weather:', e)
    }
  }

  return {
    summary,
    activities,
    stockPortfolio,
    weatherData,
    loading,
    error,
    apiToken,
    completedTasksToday,
    commitsToday,
    totalStockPnl,
    formattedStockPnl,
    isAuthenticated,
    setApiToken,
    clearApiToken,
    fetchSummary,
    fetchTimeline,
    fetchStockPortfolio,
    fetchWeather
  }
})
