<template>
  <div class="fixed inset-0 z-50 bg-black">
    <!-- 閉じるボタン -->
    <button
      @click="closeLightbox"
      class="absolute top-4 right-4 z-50 bg-white bg-opacity-20 hover:bg-opacity-40 rounded-full p-2 transition-all"
    >
      <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
      </svg>
    </button>

    <!-- メイン画像エリア -->
    <figure
      class="relative w-full h-full flex items-center justify-center"
      v-if="image"
      @touchstart="handleTouchStart"
      @touchmove="handleTouchMove"
      @touchend="handleTouchEnd"
    >
      <img
        :src="`${API_BASE_URL}/get_image?id=${image.id}&ext=${image.ext}&max_file_size=${settings.getMaxFileSize()}&quality=${settings.getQuality()}`"
        :alt="image.name"
        class="max-w-full max-h-screen object-contain select-none"
        draggable="false"
        @click="handleImageClick"
      />

      <!-- 左ナビゲーションエリア -->
      <button v-if="canGoPrevious" @click="goToPrevious"
        class="absolute top-0 left-0 w-1/5 h-full bg-transparent active:bg-white active:bg-opacity-10 cursor-pointer z-10">
        <span class="sr-only">前の画像</span>
      </button>

      <!-- 右ナビゲーションエリア -->
      <button v-if="canGoNext" @click="goToNext"
        class="absolute top-0 right-0 w-1/5 h-full bg-transparent active:bg-white active:bg-opacity-10 cursor-pointer z-10">
        <span class="sr-only">次の画像</span>
      </button>
    </figure>

    <!-- メタデータオーバーレイパネル -->
    <transition name="slide-up">
      <div
        v-if="showMetadata && image"
        class="absolute bottom-0 left-0 right-0 z-40 max-h-[60vh] overflow-y-auto"
        @touchstart.stop
        @touchmove.stop
        @click.stop
      >
        <div class="bg-black bg-opacity-75 text-white p-6">
          <!-- 評価 -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-300 mb-1">評価</label>
            <StarRating v-model="currentRating" @change="updateRating" />
          </div>

          <!-- ファイル名 -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-300 mb-1">ファイル名</label>
            <p class="text-sm text-white">{{ image.name }}</p>
          </div>

          <!-- フォルダ -->
          <div class="mb-4" v-if="image.folders && image.folders.length > 0">
            <label class="block text-sm font-medium text-gray-300 mb-1">フォルダ</label>
            <div class="flex flex-wrap gap-1">
              <button
                v-for="folderId in image.folders"
                :key="folderId"
                @click.stop="navigateToFolder(folderId)"
                class="inline-block px-2 py-1 text-xs bg-blue-900 text-blue-200 rounded hover:bg-blue-800 cursor-pointer transition-colors"
              >
                {{ getFolderName(folderId) }}
              </button>
            </div>
          </div>

          <!-- タグ -->
          <div class="mb-4" v-if="image.tags && image.tags.length > 0">
            <label class="block text-sm font-medium text-gray-300 mb-1">タグ</label>
            <div class="flex flex-wrap gap-1">
              <span v-for="tag in image.tags" :key="tag"
                class="inline-block px-2 py-1 text-xs bg-green-900 text-green-200 rounded">
                {{ tag }}
              </span>
            </div>
          </div>

          <!-- 注釈 -->
          <div class="mb-4" v-if="image.annotation">
            <label class="block text-sm font-medium text-gray-300 mb-1">注釈</label>
            <p class="text-sm text-gray-100 whitespace-pre-wrap">{{ image.annotation }}</p>
          </div>

          <!-- ファイル情報 -->
          <div class="mb-4">
            <div class="text-sm text-gray-300 space-y-1">
              <div>サイズ: {{ formatFileSize(image.size) }}</div>
              <div>形式: {{ image.ext.toUpperCase() }}</div>
              <div>解像度: {{ image.width }} × {{ image.height }}px</div>
              <div>更新日時: {{ formatDate(image.modificationTime) }}</div>
              <div>最終変更: {{ formatDate(image.lastModified) }}</div>
            </div>
          </div>

          <!-- ファイル削除 -->
          <div class="flex justify-end">
            <TrashButton
              @click.stop="moveToTrash"
              class="text-gray-300 hover:text-red-400"
              :style="{ opacity: isDeleting ? 0.5 : 1, pointerEvents: isDeleting ? 'none' : 'auto' }"
            />
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { API_BASE_URL } from '../env';
import { useSettings } from '../composables/useSettings';
import { useEagleApi } from '../composables/useEagleApi';
import { useMainStore } from '../store';
import StarRating from './common/StarRating.vue';
import TrashButton from './common/TrashButton.vue';
import { formatFileSize, formatDate } from '../modules/util';

const router = useRouter()
const route = useRoute()

// サービスの取得
const settings = useSettings()
const eagleApi = useEagleApi()
const store = useMainStore()

// 現在の画像（Piniaストアから取得）
const image = computed(() => store.getCurrentImage)

// メタデータ表示状態
const showMetadata = ref(false)

// 前の画像に移動可能かどうか
const canGoPrevious = computed(() => {
  return store.getPrevImage !== null
})

// 次の画像に移動可能かどうか
const canGoNext = computed(() => {
  return store.getNextImage !== null
})

// ルート名に応じた遷移先を取得
const getDetailRouteName = () => {
  return route.name === 'filterDetail' ? 'filterDetail' : 'folderDetail'
}

// 前の画像に移動
const goToPrevious = () => {
  if (store.getPrevImage) {
    router.push({
      name: getDetailRouteName(),
      params: { folderId: store.getCurrentFolderId, imageId: store.getPrevImage.id },
      query: route.query
    });
  }
}

// 次の画像に移動
const goToNext = () => {
  if (store.getNextImage) {
    router.push({
      name: getDetailRouteName(),
      params: { folderId: store.getCurrentFolderId, imageId: store.getNextImage.id },
      query: route.query
    });
  }
}

// 閉じる
const closeLightbox = () => {
  const folderRouteName = route.name === 'filterDetail' ? 'filter' : 'folder'
  router.push({
    name: folderRouteName,
    params: { folderId: store.getCurrentFolderId },
    query: route.query
  });
}

// 画像中央クリックでメタデータトグル
const handleImageClick = () => {
  if (swipeHandled.value) return
  showMetadata.value = !showMetadata.value
}

// --- スワイプナビゲーション ---
const touchStartX = ref(0)
const touchStartY = ref(0)
const touchCurrentX = ref(0)
const isSwiping = ref(false)
const swipeHandled = ref(false)
const SWIPE_THRESHOLD = 50

const handleTouchStart = (event: TouchEvent) => {
  const touch = event.touches[0]
  touchStartX.value = touch.clientX
  touchStartY.value = touch.clientY
  touchCurrentX.value = touch.clientX
  isSwiping.value = true
}

const handleTouchMove = (event: TouchEvent) => {
  if (!isSwiping.value) return
  const touch = event.touches[0]
  touchCurrentX.value = touch.clientX

  // 垂直スクロールが優勢な場合はスワイプをキャンセル
  const deltaX = Math.abs(touch.clientX - touchStartX.value)
  const deltaY = Math.abs(touch.clientY - touchStartY.value)
  if (deltaY > deltaX) {
    isSwiping.value = false
  }
}

const handleTouchEnd = () => {
  if (!isSwiping.value) return

  const deltaX = touchCurrentX.value - touchStartX.value

  if (Math.abs(deltaX) > SWIPE_THRESHOLD) {
    swipeHandled.value = true
    setTimeout(() => { swipeHandled.value = false }, 300)

    if (deltaX < 0) {
      // 左スワイプ → 次の画像
      goToNext()
    } else {
      // 右スワイプ → 前の画像
      goToPrevious()
    }
  }

  isSwiping.value = false
}

// --- キーボードナビゲーション ---
const handleKeydown = (event: KeyboardEvent) => {
  switch (event.key) {
    case 'ArrowLeft':
      event.preventDefault()
      goToPrevious()
      break
    case 'ArrowRight':
      event.preventDefault()
      goToNext()
      break
    case 'Escape':
      event.preventDefault()
      if (showMetadata.value) {
        showMetadata.value = false
      } else {
        closeLightbox()
      }
      break
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

// 評価の状態管理
const currentRating = ref(image.value?.star || 0)

// 削除中フラグ
const isDeleting = ref(false)

// 評価値の更新とAPI呼び出し
const updateRating = async (rating: number) => {
  if (!image.value) return

  const oldRating = currentRating.value
  try {
    await eagleApi.updateItem(image.value.id, {
      star: rating
    })
  } catch (error) {
    currentRating.value = oldRating
    console.error('評価の更新に失敗しました:', error)
  }
}

// フォルダIDからフォルダ名を取得
const getFolderName = (folderId: string): string => {
  const findFolder = (folders: any[], id: string): any => {
    for (const folder of folders) {
      if (folder.id === id) return folder;
      if (folder.children) {
        const found = findFolder(folder.children, id);
        if (found) return found;
      }
    }
    return null;
  }

  const folder = findFolder(store.getFolders, folderId);
  return folder ? folder.name : folderId;
};

// フォルダに移動
const navigateToFolder = (folderId: string) => {
  router.push({ name: 'folder', params: { folderId } });
};

// ファイルをゴミ箱に移動
const moveToTrash = async () => {
  if (!image.value || isDeleting.value) return

  // 削除確認ダイアログ
  const confirmed = window.confirm(`「${image.value.name}」をゴミ箱に移動しますか？`)
  if (!confirmed) return

  isDeleting.value = true

  try {
    await eagleApi.moveToTrash([image.value.id])

    // 成功時はLightboxを閉じる
    closeLightbox()
  } catch (error) {
    console.error('ファイルの削除に失敗しました:', error)
    window.alert('ファイルの削除に失敗しました。')
  } finally {
    isDeleting.value = false
  }
};

// 画像が変更されたときに評価値を更新
watch(() => image.value, (newImage) => {
  currentRating.value = newImage?.star || 0
}, { immediate: true })

</script>

<style scoped>
.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.3s ease-out;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
}
</style>
