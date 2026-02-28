import { ref } from 'vue'
import { useSettings } from './useSettings'
import { useEagleApi } from './useEagleApi'
import { useMainStore } from '../store'
import { API_BASE_URL, ITEM_GET_COUNT } from '../env'

// シングルトンインスタンス
let instance: ReturnType<typeof createAutoReload> | null = null

function createAutoReload() {
  const settings = useSettings()
  const eagleApi = useEagleApi()
  const store = useMainStore()

  // 最後に確認した先頭アイテムのスナップショット（ID + 件数）
  const lastSnapshot = ref<{ firstId: string; count: number } | null>(null)

  // ポーリングタイマーID
  let pollingTimer: ReturnType<typeof setInterval> | null = null

  // ポーリングが動作中かどうか
  const isPolling = ref(false)

  /**
   * 現在のフォルダの先頭アイテムを軽量に取得してスナップショットを返す
   */
  const fetchSnapshot = async (): Promise<{ firstId: string; count: number } | null> => {
    const currentFolderId = store.getCurrentFolderId
    if (!currentFolderId) return null

    try {
      // 少量だけ取得して変更検知に使う
      const items = await eagleApi.loadImages({
        folderId: currentFolderId,
        limit: 1,
        offset: 0,
      })
      return {
        firstId: items.length > 0 ? items[0].id : '',
        count: items.length,
      }
    } catch (error) {
      console.warn('[AutoReload] Error fetching snapshot:', error)
      return null
    }
  }

  /**
   * 変更を検知して画像リストをリロード
   */
  const checkForChanges = async () => {
    // ローディング中はスキップ（無限スクロールの途中など）
    if (eagleApi.isImagesLoading.value) {
      return
    }

    const currentSnapshot = await fetchSnapshot()
    if (currentSnapshot === null) return

    // 初回は基準値を設定するだけ（リロードしない）
    if (lastSnapshot.value === null) {
      lastSnapshot.value = currentSnapshot
      return
    }

    // 変更を検知（先頭アイテムIDまたは件数が異なれば変更あり）
    const changed = currentSnapshot.firstId !== lastSnapshot.value.firstId ||
      currentSnapshot.count !== lastSnapshot.value.count

    if (changed) {
      console.log('[AutoReload] Change detected, reloading...')
      lastSnapshot.value = currentSnapshot
      await reloadCurrentView()
    }
  }

  /**
   * 現在の表示を非破壊的にリロード
   */
  const reloadCurrentView = async () => {
    const currentFolderId = store.getCurrentFolderId
    if (!currentFolderId) return

    // Lightboxが開いている場合はリロードしない
    if (store.getCurrentImage) {
      console.log('[AutoReload] Skipping reload: Lightbox is open')
      return
    }

    console.log('[AutoReload] Reloading images for folder:', currentFolderId)

    // 現在のスクロール位置を記憶
    const scrollY = window.scrollY

    // フルページを取得して置き換え
    const newImages = await eagleApi.loadImages({
      folderId: currentFolderId,
      limit: ITEM_GET_COUNT,
      offset: 0,
    })

    store.setImages(newImages)
    store.resetCurrentPageCount()
    eagleApi.hasMoreItems.value = newImages.length >= ITEM_GET_COUNT
    store.addCurrentPageCount()

    // スクロール位置を復元
    requestAnimationFrame(() => {
      window.scrollTo(0, Math.min(scrollY, document.body.scrollHeight))
    })
  }

  /**
   * ポーリングを開始
   */
  const startPolling = () => {
    stopPolling()

    if (!settings.getAutoReload()) {
      return
    }

    const intervalMs = settings.getAutoReloadInterval() * 1000
    isPolling.value = true

    // 初回チェック（基準値の設定）
    checkForChanges()

    pollingTimer = setInterval(checkForChanges, intervalMs)
    console.log(`[AutoReload] Polling started (interval: ${intervalMs}ms)`)
  }

  /**
   * ポーリングを停止
   */
  const stopPolling = () => {
    if (pollingTimer !== null) {
      clearInterval(pollingTimer)
      pollingTimer = null
    }
    isPolling.value = false
  }

  /**
   * ポーリングをリスタート（設定変更時）
   */
  const restartPolling = () => {
    stopPolling()
    startPolling()
  }

  /**
   * modificationTimeの基準値をリセット（フォルダ切替時に呼び出す）
   */
  const resetBaseline = () => {
    lastSnapshot.value = null
  }

  // タブ表示/非表示でポーリングを制御（モバイル最適化）
  const handleVisibilityChange = () => {
    if (document.hidden) {
      stopPolling()
    } else {
      checkForChanges()
      startPolling()
    }
  }

  /**
   * visibilitychangeリスナーを登録
   */
  const setupVisibilityListener = () => {
    document.addEventListener('visibilitychange', handleVisibilityChange)
  }

  return {
    isPolling,
    lastSnapshot,
    startPolling,
    stopPolling,
    restartPolling,
    resetBaseline,
    checkForChanges,
    setupVisibilityListener,
  }
}

export function useAutoReload() {
  if (!instance) {
    instance = createAutoReload()
  }
  return instance
}
