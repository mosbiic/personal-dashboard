<script setup>
import { onMounted } from 'vue'
import { useDashboardStore } from './stores/dashboard'
import DashboardHeader from './components/DashboardHeader.vue'
import TimelineView from './components/TimelineView.vue'
import StatsGrid from './components/StatsGrid.vue'
import StocksView from './components/StocksView.vue'

const dashboardStore = useDashboardStore()

onMounted(() => {
  dashboardStore.fetchSummary()
})
</script>

<template>
  <div class="min-h-screen">
    <DashboardHeader />
    <main class="container mx-auto px-4 py-6">
      <StatsGrid />
      <StocksView class="mt-6" />
      <TimelineView class="mt-6" />
    </main>
  </div>
</template>
