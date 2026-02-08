<script setup>
import { ref } from 'vue'

const sources = ref([
  { name: 'Trello', connected: false, icon: '📋' },
  { name: 'GitHub', connected: false, icon: '🐙' },
  { name: '股票', connected: false, icon: '📈' },
  { name: '天气', connected: false, icon: '🌤️' }
])

const apiKeys = ref({
  trelloKey: '',
  trelloToken: '',
  githubToken: '',
  weatherKey: ''
})

function saveSettings() {
  // Save settings to backend
  alert('设置已保存')
}
</script>

<template>
  <div class="max-w-2xl mx-auto">
    <h2 class="text-2xl font-bold text-white mb-6">设置</h2>

    <!-- Data Sources Status -->
    <div class="bg-slate-800 rounded-xl border border-slate-700 p-6 mb-6">
      <h3 class="text-lg font-semibold text-white mb-4">数据源状态</h3>
      
      <div class="grid grid-cols-2 gap-4">
        <div
          v-for="source in sources"
          :key="source.name"
          class="flex items-center gap-3 p-3 bg-slate-700/50 rounded-lg"
        >
          <span class="text-2xl">{{ source.icon }}</span>
          <div class="flex-1">
            <p class="text-white font-medium">{{ source.name }}</p>
            <p :class="['text-xs', source.connected ? 'text-green-400' : 'text-slate-400']">
              {{ source.connected ? '已连接' : '未配置' }}
            </p>
          </div>
          <div
            :class="['w-2 h-2 rounded-full', source.connected ? 'bg-green-500' : 'bg-slate-500']"
          />
        </div>
      </div>
    </div>

    <!-- API Keys -->
    <div class="bg-slate-800 rounded-xl border border-slate-700 p-6">
      <h3 class="text-lg font-semibold text-white mb-4">API 配置</h3>

      <div class="space-y-4">
        <div>
          <label class="block text-sm text-slate-400 mb-1">Trello API Key</label>
          <input
            v-model="apiKeys.trelloKey"
            type="password"
            class="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
          />
        </div>

        <div>
          <label class="block text-sm text-slate-400 mb-1">Trello Token</label>
          <input
            v-model="apiKeys.trelloToken"
            type="password"
            class="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
          />
        </div>

        <div>
          <label class="block text-sm text-slate-400 mb-1">GitHub Token</label>
          <input
            v-model="apiKeys.githubToken"
            type="password"
            class="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
          />
        </div>

        <div>
          <label class="block text-sm text-slate-400 mb-1">OpenWeather API Key</label>
          <input
            v-model="apiKeys.weatherKey"
            type="password"
            class="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      <button
        @click="saveSettings"
        class="mt-6 w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-medium transition"
      >
        保存设置
      </button>
    </div>
  </div>
</template>
