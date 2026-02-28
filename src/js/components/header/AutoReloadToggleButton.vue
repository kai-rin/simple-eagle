<template>
  <button
    @click="toggle"
    class="p-2 rounded-lg transition-colors duration-200"
    :class="isActive
      ? 'bg-green-100 dark:bg-green-900 hover:bg-green-200 dark:hover:bg-green-800'
      : 'hover:bg-gray-100 dark:hover:bg-gray-700'"
    :title="isActive ? '自動リロード: ON (クリックで無効化)' : '自動リロード: OFF (クリックで有効化)'"
  >
    <!-- 回転矢印アイコン -->
    <svg
      class="w-5 h-5 transition-colors duration-200"
      :class="isActive ? 'text-green-600 dark:text-green-400' : 'text-gray-400 dark:text-gray-500'"
      viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
    >
      <path d="M21.5 2v6h-6" />
      <path d="M2.5 22v-6h6" />
      <path d="M2.5 11.5a10 10 0 0 1 18.4-4.5L21.5 8" />
      <path d="M21.5 12.5a10 10 0 0 1-18.4 4.5L2.5 16" />
    </svg>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSettings } from '../../composables/useSettings'
import { useAutoReload } from '../../composables/useAutoReload'

const settings = useSettings()
const autoReload = useAutoReload()

const isActive = computed(() => settings.getAutoReload())

const toggle = () => {
  const newValue = !isActive.value
  settings.setAutoReload(newValue)
  settings.saveSettings()
  if (newValue) {
    autoReload.restartPolling()
  } else {
    autoReload.stopPolling()
  }
}
</script>
