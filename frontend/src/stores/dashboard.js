import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'

const API_BASE = '/api'

export const useDashboardStore = defineStore('dashboard', () => {
  // State
  const summary = ref(null)
  const activities = ref([])
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const completedTasksToday = computed(() => summary.value?.trello?.completed_today || 0)
  const commitsToday = computed(() => summary.value?.github?.commits_today || 0)

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

  return {
    summary,
    activities,
    loading,
    error,
    completedTasksToday,
    commitsToday,
    fetchSummary,
    fetchTimeline
  }
})
