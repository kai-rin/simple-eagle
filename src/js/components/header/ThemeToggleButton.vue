<template>
  <button
    @click="cycleTheme"
    class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200"
    :title="themeTitle"
  >
    <!-- 太陽アイコン (light) -->
    <svg v-if="currentTheme === 'light'"
      class="w-5 h-5 text-gray-600 dark:text-gray-300" viewBox="0 0 24 24" fill="none" stroke="currentColor">
      <circle cx="12" cy="12" r="5" stroke-width="2"/>
      <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"
        stroke-width="2" stroke-linecap="round"/>
    </svg>
    <!-- 月アイコン (dark) -->
    <svg v-else-if="currentTheme === 'dark'"
      class="w-5 h-5 text-gray-600 dark:text-gray-300" viewBox="0 0 24 24" fill="currentColor">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
    </svg>
    <!-- モニターアイコン (system) -->
    <svg v-else
      class="w-5 h-5 text-gray-600 dark:text-gray-300" viewBox="0 0 24 24" fill="none" stroke="currentColor">
      <rect x="2" y="3" width="20" height="14" rx="2" stroke-width="2"/>
      <path d="M8 21h8M12 17v4" stroke-width="2" stroke-linecap="round"/>
    </svg>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSettings } from '../../composables/useSettings'
import type { TTheme } from '../../composables/useSettings'

const settings = useSettings()
const currentTheme = computed(() => settings.getTheme())

const themeTitle = computed(() => {
  switch (currentTheme.value) {
    case 'light': return 'ライトモード (クリックで切替)'
    case 'dark': return 'ダークモード (クリックで切替)'
    default: return 'システム設定に従う (クリックで切替)'
  }
})

// light → dark → system のサイクル
const cycleTheme = () => {
  const order: TTheme[] = ['light', 'dark', 'system']
  const currentIndex = order.indexOf(currentTheme.value)
  const nextIndex = (currentIndex + 1) % order.length
  settings.setTheme(order[nextIndex])
}
</script>
