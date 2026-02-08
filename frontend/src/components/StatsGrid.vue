<script setup>
import { useDashboardStore } from '../stores/dashboard'

const dashboard = useDashboardStore()

const stats = [
  {
    title: '今日完成',
    value: () => dashboard.completedTasksToday,
    icon: '📋',
    color: 'bg-green-500',
    source: 'Trello'
  },
  {
    title: '代码提交',
    value: () => dashboard.commitsToday,
    icon: '🐙',
    color: 'bg-purple-500',
    source: 'GitHub'
  },
  {
    title: '股票盈亏',
    value: () => '+0.0%',
    icon: '📈',
    color: 'bg-blue-500',
    source: 'Stocks'
  },
  {
    title: '天气',
    value: () => '--°C',
    icon: '🌤️',
    color: 'bg-yellow-500',
    source: 'Weather'
  }
]
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
    <div
      v-for="stat in stats"
      :key="stat.title"
      class="bg-slate-800 rounded-xl p-5 border border-slate-700 hover:border-slate-600 transition"
    >
      <div class="flex items-start justify-between">
        <div>
          <p class="text-slate-400 text-sm">{{ stat.title }}</p>
          <p class="text-2xl font-bold text-white mt-1">{{ typeof stat.value === 'function' ? stat.value() : stat.value }}</p>
          <p class="text-xs text-slate-500 mt-2">{{ stat.source }}</p>
        </div>
        <div :class="[stat.color, 'w-12 h-12 rounded-lg flex items-center justify-center text-2xl']">
          {{ stat.icon }}
        </div>
      </div>
    </div>
  </div>
</template>
