<script setup>
import StatsGrid from '../components/StatsGrid.vue'
import TimelineView from '../components/TimelineView.vue'
</script>

<template>
  <div class="space-y-6">
    <StatsGrid />
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2">
        <TimelineView />
      </div>
      <div class="bg-slate-800 rounded-xl p-4 border border-slate-700">
        <h3 class="text-lg font-semibold text-white mb-4">快捷操作</h3>
        <div class="space-y-2">
          <button class="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 rounded-lg text-white text-sm transition">
            同步 Trello
          </button>
          <button class="w-full py-2 px-4 bg-slate-700 hover:bg-slate-600 rounded-lg text-white text-sm transition">
            同步 GitHub
          </button>
          <button class="w-full py-2 px-4 bg-slate-700 hover:bg-slate-600 rounded-lg text-white text-sm transition">
            刷新天气
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
