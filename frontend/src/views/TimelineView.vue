<script setup>
import { ref } from 'vue'

const periods = ['今天', '本周', '本月']
const currentPeriod = ref('今天')
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-bold text-white">完整时间轴</h2>
      
      <div class="flex bg-slate-800 rounded-lg p-1">
        <button
          v-for="period in periods"
          :key="period"
          @click="currentPeriod = period"
          :class="[
            'px-4 py-2 rounded-md transition',
            currentPeriod === period
              ? 'bg-blue-600 text-white'
              : 'text-slate-400 hover:text-white'
          ]"
        >
          {{ period }}
        </button>
      </div>
    </div>

    <div class="bg-slate-800 rounded-xl border border-slate-700 p-6">
      <!-- Timeline content will go here -->
      <div class="text-center py-12 text-slate-500">
        <p>时间轴详细视图开发中... 🔨</p>
      </div>
    </div>
  </div>
</template>
