<script setup>
import { ref, onMounted } from 'vue'
import { useDashboardStore } from '../stores/dashboard'

const dashboard = useDashboardStore()
const currentPeriod = ref('today')

const periods = [
  { key: 'today', label: '今天' },
  { key: 'week', label: '本周' },
  { key: 'month', label: '本月' }
]

onMounted(() => {
  dashboard.fetchTimeline(currentPeriod.value)
})

function changePeriod(period) {
  currentPeriod.value = period
  dashboard.fetchTimeline(period)
}
</script>

<template>
  <div class="bg-slate-800 rounded-xl border border-slate-700">
    <div class="p-4 border-b border-slate-700 flex items-center justify-between">
      <h2 class="text-lg font-semibold text-white">活动时间轴</h2>
      
      <div class="flex bg-slate-700 rounded-lg p-1">
        <button
          v-for="period in periods"
          :key="period.key"
          @click="changePeriod(period.key)"
          :class="[
            'px-3 py-1 text-sm rounded-md transition',
            currentPeriod === period.key
              ? 'bg-slate-600 text-white'
              : 'text-slate-400 hover:text-white'
          ]"
        >
          {{ period.label }}
        </button>
      </div>
    </div>

    <div class="p-4">
      <div v-if="dashboard.loading" class="text-center py-8 text-slate-400">
        加载中...
      </div>

      <div v-else-if="dashboard.activities.length === 0" class="text-center py-8 text-slate-500">
        <p>暂无活动记录</p>
        <p class="text-sm mt-2">配置数据源后开始追踪</p>
      </div>

      <div v-else class="space-y-4">
        <!-- Activity items will go here -->
        <div
          v-for="activity in dashboard.activities"
          :key="activity.id"
          class="flex gap-4 p-3 rounded-lg hover:bg-slate-700/50 transition"
        >
          <div class="w-10 h-10 rounded-full bg-slate-700 flex items-center justify-center">
            {{ activity.icon || '📝' }}
          </div>
          <div class="flex-1">
            <p class="text-white font-medium">{{ activity.title }}</p>
            <p class="text-sm text-slate-400">{{ activity.description }}</p>
            <p class="text-xs text-slate-500 mt-1">{{ activity.time }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
