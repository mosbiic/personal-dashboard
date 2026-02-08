<script setup>
import { useDashboardStore } from '../stores/dashboard'

const dashboard = useDashboardStore()

function formatTemp(temp) {
  if (temp === null || temp === undefined) return '--'
  return `${Math.round(temp)}°C`
}
</script>

<template>
  <div v-if="dashboard.weatherData" class="flex items-center gap-4 bg-slate-700/50 rounded-lg px-4 py-2">
    <!-- 当前天气 -->
    <div class="flex items-center gap-2">
      <span class="text-2xl">{{ dashboard.weatherData.current.icon }}</span>
      <div>
        <p class="text-white font-medium">{{ formatTemp(dashboard.weatherData.current.temperature) }}</p>
        <p class="text-xs text-slate-400">{{ dashboard.weatherData.current.description }}</p>
      </div>
    </div>
    
    <!-- 分隔线 -->
    <div class="w-px h-8 bg-slate-600"></div>
    
    <!-- 位置信息 -->
    <div class="text-sm">
      <p class="text-slate-300">{{ dashboard.weatherData.location }}</p>
      <p class="text-xs text-slate-500">湿度 {{ dashboard.weatherData.current.humidity }}%</p>
    </div>
    
    <!-- 未来3天预报（简化显示） -->
    <div class="flex gap-2 ml-2">
      <div 
        v-for="(day, index) in dashboard.weatherData.forecast?.slice(1, 4)" 
        :key="index"
        class="text-center px-2"
      >
        <p class="text-xs text-slate-500">{{ new Date(day.date).getDate() }}日</p>
        <span class="text-lg">{{ day.icon || '🌤️' }}</span>
        <p class="text-xs text-slate-400">{{ Math.round(day.max_temp) }}°</p>
      </div>
    </div>
  </div>
  
  <!-- 加载状态 -->
  <div v-else-if="dashboard.loading" class="text-slate-500 text-sm">
    加载天气...
  </div>
</template>
