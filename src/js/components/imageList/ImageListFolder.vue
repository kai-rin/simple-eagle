<template>
  <div 
    class="c-grid-item relative aspect-square"
  >
    <div
      class="w-full h-full bg-blue-50 dark:bg-blue-950 rounded overflow-hidden relative cursor-pointer hover:bg-blue-100 dark:hover:bg-blue-900 transition-colors flex flex-col items-center justify-center"
      @click="handleFolderClick"
    >
      <!-- フォルダーアイコン -->
      <div class="text-blue-500 text-2xl mb-2">📁</div>
      
      <!-- フォルダー名 -->
      <span class="text-xs text-blue-700 dark:text-blue-300 text-center px-2 truncate w-full">
        {{ childFolder.name }}
      </span>
      
      <!-- 画像数 -->
      <span class="text-xs text-blue-500 dark:text-blue-400 mt-1">
        ({{ childFolder.imageCount }})
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
// import { useMainStore } from '../store'
import { useRouter } from 'vue-router';
import type { TFolderItem } from '../../types'

// const store = useMainStore()
const router = useRouter();

const props = defineProps<{
  childFolder: TFolderItem;
}>()

// フォルダークリック時の処理
const handleFolderClick = () => {
  // store.setCurrentFolder(props.childFolder.id);
  router.push({ name: 'folder', params: { folderId: props.childFolder.id } });
}

</script>
