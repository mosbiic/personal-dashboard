<script setup>
import { ref, watch } from 'vue'
import { useDashboardStore } from '../stores/dashboard'

const dashboard = useDashboardStore()
const tokenInput = ref('')
const showAuth = ref(false)

// 检查是否需要显示认证
watch(() => dashboard.error, (err) => {
  if (err && (err.includes('401') || err.includes('403'))) {
    showAuth.value = true
  }
})

function handleSubmit() {
  if (tokenInput.value.trim()) {
    dashboard.setApiToken(tokenInput.value.trim())
    showAuth.value = false
    // 刷新数据
    dashboard.fetchSummary()
  }
}

function handleLogout() {
  dashboard.clearApiToken()
  tokenInput.value = ''
}
</script>

<template>
  <div class="relative">
    <!-- Token 设置按钮 -->
    <button 
      v-if="!dashboard.isAuthenticated"
      @click="showAuth = true"
      class="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm transition flex items-center gap-2"
    >
      <span>🔐</span>
      <span>设置 API Token</span>
    </button>
    
    <button 
      v-else
      @click="handleLogout"
      class="px-4 py-2 bg-green-700 hover:bg-green-600 text-white rounded-lg text-sm transition flex items-center gap-2"
    >
      <span>✅</span>
      <span>已认证</span>
    </button>

    <!-- Token 输入弹窗 -->
    <div 
      v-if="showAuth" 
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="showAuth = false"
    >
      <div class="bg-slate-800 rounded-xl p-6 w-full max-w-md mx-4 border border-slate-700">
        <h3 class="text-xl font-semibold text-white mb-4">API Token 认证</h3>
        
        <p class="text-slate-400 text-sm mb-4">
          请输入访问 Dashboard API 的 Token。
          Token 将被保存在浏览器本地存储中。
        </p>
        
        <input
          v-model="tokenInput"
          type="password"
          placeholder="输入 API Token..."
          class="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          @keyup.enter="handleSubmit"
        />
        
        <div class="flex gap-3 mt-4">
          <button
            @click="showAuth = false"
            class="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition"
          >
            取消
          </button>
          <button
            @click="handleSubmit"
            class="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition"
            :disabled="!tokenInput.trim()"
          >
            确认
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
