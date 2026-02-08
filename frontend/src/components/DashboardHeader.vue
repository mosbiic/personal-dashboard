<script setup>
import { onMounted } from 'vue'
import { useDashboardStore } from '../stores/dashboard'
import TokenAuth from './TokenAuth.vue'
import WeatherWidget from './WeatherWidget.vue'

const dashboard = useDashboardStore()

onMounted(() => {
  dashboard.fetchWeather()
})
</script>

<template>
  <header class="bg-slate-800 border-b border-slate-700">
    <div class="container mx-auto px-4 py-4">
      <div class="flex items-center justify-between">
        <!-- Logo -->
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
            <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
            </svg>
          </div>
          <div>
            <h1 class="text-xl font-bold text-white">个人仪表盘</h1>
            <p class="text-sm text-slate-400">{{ new Date().toLocaleDateString('zh-CN') }}</p>
          </div>
        </div>

        <!-- 中间：天气小组件 -->
        <WeatherWidget />

        <!-- 右侧：导航 + Token -->
        <div class="flex items-center gap-6">
          <nav class="flex gap-4">
            <router-link to="/" class="text-slate-300 hover:text-white transition" active-class="text-blue-400">概览</router-link>
            <router-link to="/timeline" class="text-slate-300 hover:text-white transition" active-class="text-blue-400">时间轴</router-link>
            <router-link to="/settings" class="text-slate-300 hover:text-white transition" active-class="text-blue-400">设置</router-link>
          </nav>
          
          <TokenAuth />
        </div>
      </div>
    </div>
  </header>
</template>
