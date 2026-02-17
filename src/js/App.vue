<template>
  <!-- 認証チェック中 -->
  <div v-if="authState === 'checking'" />

  <!-- ログイン画面 -->
  <LoginView v-else-if="authState === 'login'" @authenticated="onAuthenticated" />

  <!-- メインUI -->
  <div v-else class="container mx-auto pl-4 pr-4 pb-4 min-h-screen">
    <!-- ヘッダーバー -->
    <Header />

    <!-- 画像一覧表示 -->
    <ImageListView />

    <!-- フォルダー一覧モーダル -->
    <FolderTreeView />

    <!-- 設定画面 -->
    <SettingView />

    <!-- フィルター条件設定モーダル -->
    <FilterView />

    <!-- 選択モードで使用するアクション -->
    <ActionView />

    <!-- ルータービュー -->
    <router-view />

  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import ImageListView from './components/imageList/ImageListView.vue';
import Header from './components/header/Header.vue';
import FolderTreeView from './components/folderTree/FolderTreeView.vue';
import SettingView from './components/SettingView.vue'
import FilterView from './components/FilterView.vue';
import ActionView from './components/action/ActionView.vue';
import LoginView from './components/LoginView.vue';
import { useEagleApi } from './composables/useEagleApi';
import { useMainStore } from './store';
import { useRoute, useRouter } from 'vue-router';
import { ITEM_GET_COUNT } from './env';

// 認証状態: 'checking' | 'login' | 'authenticated'
const authState = ref<'checking' | 'login' | 'authenticated'>('checking');

// サービスの取得
const eagleApi = useEagleApi();
const store = useMainStore();
const route = useRoute();
const router = useRouter();

const loadImages = async (folderId: string, /*searchParams?: any*/) => {
  if ( folderId === store.getCurrentFolderId ) return;

  console.log("[App.vue] Loading images:", folderId, store.getCurrentFolderId);
  store.setCurrentFolderId(folderId as string);

  // 検索パラメーターは現状使っていないので通常呼び出しのみ
  await eagleApi.loadImagesInfinite({
    folderId,
    limit: ITEM_GET_COUNT,
    offset: 0,
  });

  // if (searchParams) {
  //   // 検索パラメーターがある場合
  //   await eagleApi.loadImagesInfinite({
  //     folderId,
  //     limit: 400,
  //     orderBy: searchParams.orderBy,
  //     keyword: searchParams.keyword,
  //     ext: searchParams.ext,
  //     tags: searchParams.tags
  //   });
  // } else {
  //   // 通常のフォルダー表示
  //   await eagleApi.loadImagesInfinite({
  //     folderId,
  //     limit: 400
  //   });
  // }
}

// URLが変更されたらstoreに反映
watch(
  [() => route.params.folderId, () => route.params.imageId, () => route.name, () => route.query],
  async ([folderId, imageId, routeName, query], [prevFolderId, prevImageId, prevRouteName, prevQuery]) => {
    // 認証完了前はAPI呼び出しをしない
    if (authState.value !== 'authenticated') return;

    console.log("[App.vue] Folder ID from URL:", folderId, routeName, query);
    // console.log("Route name:", routeName);
    // console.log("Query parameters:", query);
    // console.log("Query parameters Old:", prevQuery);

    folderId = folderId as string || "all";

    // フォルダーまたは検索条件の変更
    if ( folderId !== prevFolderId ) {
      console.log("Loading images for:", { folderId });
      // 通常のフォルダールートの場合
      loadImages(folderId);
    }


    // フィルタ条件を sotre に設定
    if(routeName === 'filter' || routeName === 'filterDetail') {
      if ( JSON.stringify(query) !== JSON.stringify(prevQuery) ) {
        const stars = query.stars ? (Array.isArray(query.stars) ? query.stars.map(Number) : [Number(query.stars)]) : [];
        const exts = query.exts ? (Array.isArray(query.exts) ? query.exts.filter(Boolean) as string[] : [query.exts].filter(Boolean) as string[]) : [];
        const tags = query.tags ? (Array.isArray(query.tags) ? query.tags.filter(Boolean) as string[] : [query.tags].filter(Boolean) as string[]) : [];

        store.setCurrentFilter({
          stars,
          exts,
          keyword: query.keyword as string || '',
          tags
        });
        // console.log("Filter applied:", store.getCurrentFilter);
      }
    } else {
      store.setCurrentFilter(null);
    }

    if (imageId !== prevImageId && imageId && typeof imageId === 'string') {
      // 初期読み込みが完了している場合は即座に設定
      if (!eagleApi.isImagesLoading.value) {
        store.setCurrentImage(imageId);
      }
    }
  },
)

// 認証後のデータ読み込み
const loadInitialData = async () => {
  await router.isReady()

  // フォルダー一覧の読み込み
  await eagleApi.loadFolders();

  // 画像の初期読み込み
  const folderId = route.params.folderId as string || "all";
  await loadImages(folderId as string);

  // 初期読み込み完了後、URLにimageIdがある場合は設定
  const imageId = route.params.imageId
  if (imageId && typeof imageId === 'string') {
    store.setCurrentImage(imageId)
  }
}

// ログイン成功時のコールバック
const onAuthenticated = async () => {
  authState.value = 'authenticated';
  await loadInitialData();
}

// 初期読み込み
onMounted(async () => {
  // 認証チェック
  try {
    const res = await fetch('/api/auth/check');
    if (res.ok) {
      authState.value = 'authenticated';
      await loadInitialData();
    } else {
      authState.value = 'login';
    }
  } catch {
    authState.value = 'login';
  }
})

</script>
