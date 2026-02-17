<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-950">
    <div class="bg-white dark:bg-gray-800 p-8 rounded-lg shadow-md w-full max-w-sm">
      <h1 class="text-2xl font-bold mb-6 text-center dark:text-white">Simple Eagle</h1>
      <form @submit.prevent="handleLogin">
        <div class="mb-4">
          <label for="password" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            パスワード
          </label>
          <input
            id="password"
            v-model="password"
            type="password"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 dark:text-white"
            placeholder="パスワードを入力"
            autofocus
          />
        </div>
        <p v-if="errorMessage" class="mb-4 text-sm text-red-600">{{ errorMessage }}</p>
        <button
          type="submit"
          :disabled="isLoading"
          class="w-full px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {{ isLoading ? 'ログイン中...' : 'ログイン' }}
        </button>
      </form>

      <!-- LAN アクセス情報 -->
      <div v-if="lanUrl" class="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700 text-center">
        <p class="text-xs text-gray-500 dark:text-gray-400 mb-1">スマホからアクセス</p>
        <a :href="lanUrl" class="text-sm text-blue-600 underline break-all">{{ lanUrl }}</a>
        <img
          :src="`/api/auth/qrcode?url=${encodeURIComponent(lanUrl)}`"
          alt="QR Code"
          class="mx-auto mt-3 w-48 h-48"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const emit = defineEmits<{
  authenticated: []
}>()

const password = ref('')
const errorMessage = ref('')
const isLoading = ref(false)
const lanUrl = ref('')

const handleLogin = async () => {
  errorMessage.value = ''
  isLoading.value = true

  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: password.value }),
    })

    if (response.ok) {
      emit('authenticated')
    } else {
      errorMessage.value = 'パスワードが正しくありません'
    }
  } catch {
    errorMessage.value = 'サーバーに接続できません'
  } finally {
    isLoading.value = false
  }
}

onMounted(async () => {
  try {
    const res = await fetch('/api/auth/server-info')
    if (res.ok) {
      const data = await res.json()
      lanUrl.value = data.url
    }
  } catch {
    // サーバー情報取得失敗時は非表示のまま
  }
})
</script>
