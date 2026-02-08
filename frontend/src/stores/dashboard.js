import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'

const API_BASE = '/api'

// 本地开发模式默认 Token
const LOCAL_DEV_TOKEN = '43f4404377d1684d88fabbe5a2eb852af2d0f91955b9a6bd1d6aa26fed34ba9d'

// Cloudflare Access 模式检测 - 如果本地没有 token，假设使用 CF Access
const getApiToken = () => {
  return localStorage.getItem('dashboard_api_token') || import.meta.env.VITE_API_TOKEN || ''
}

// 检测是否需要自动设置本地开发 Token
const autoSetLocalToken = () => {
  const existingToken = localStorage.getItem('dashboard_api_token') || import.meta.env.VITE_API_TOKEN
  if (!existingToken) {
    // 没有 Token，尝试使用本地开发 Token
    localStorage.setItem('dashboard_api_token', LOCAL_DEV_TOKEN)
    return LOCAL_DEV_TOKEN
  }
  return existingToken
}

const IS_CF_ACCESS = !getApiToken()

// 配置 axios 拦截器添加 token
const setupAxiosInterceptors = () => {
  axios.interceptors.request.use((config) => {
    // 只在本地 Token 模式下添加认证头
    const token = getApiToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    // Cloudflare Access 模式下不添加任何 header，后端会检查 CF-Access-Authenticated-User-Email
    return config
  })
  
  axios.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401 || error.response?.status === 403) {
        // 只在本地 Token 模式下处理 401/403
        if (!IS_CF_ACCESS) {
          localStorage.removeItem('dashboard_api_token')
          console.error('API Token 无效或已过期')
        }
        // Cloudflare Access 模式下 CF 会自动处理重定向
      }
      return Promise.reject(error)
    }
  )
}

setupAxiosInterceptors()

export const useDashboardStore = defineStore('dashboard', () => {
  // 自动设置本地开发 Token（如果未设置）
  autoSetLocalToken()
  
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
