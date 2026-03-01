import { ref, nextTick } from 'vue'
import { useSettings } from './useSettings'
import { useEagleApi } from './useEagleApi'
import { useMainStore } from '../store'
import { ITEM_GET_COUNT } from '../env'

// シングルトンインスタンス
let instance: ReturnType<typeof createAutoReload> | null = null

function createAutoReload() {
  const settings = useSettings()
  const eagleApi = useEagleApi()
  const store = useMainStore()

  // 最後に確認したアイテムシグネチャ（最新アイテムの id:modificationTime）
  const lastSignature = ref<string | null>(null)

  // ポーリングタイマーID
  let pollingTimer: ReturnType<typeof setInterval> | null = null

  // ポーリングが動作中かどうか
  const isPolling = ref(false)

  // リロード中フラグ（IntersectionObserver競合防止用）
  const isReloading = ref(false)

  // 重複実行を防ぐガード
  let isChecking = false

  // handleVisibilityChange の再入防止ガード
  let isHandlingVisibility = false

  // visibilitychange リスナーの参照
  let visibilityHandler: (() => void) | null = null

  // visible 遷移のデバウンスタイマー
  let visibilityDebounceTimer: ReturnType<typeof setTimeout> | null = null

  /**
   * 最新アイテムのシグネチャを取得して変更があったか判定
   * Eagle の library-info の modificationTime は画像追加で更新されないため、
   * 最新アイテムの ID + modificationTime を比較して変更を検出する
   * @returns true = 変更あり, false = 変更なし, null = 取得失敗
   */
  const checkItemSignature = async (): Promise<boolean | null> => {
    const currentFolderId = store.getCurrentFolderId
    const signature = await eagleApi.fetchLatestItemSignature(currentFolderId || undefined)
    if (signature === null) return null

    // 初回は基準値を設定するだけ
    if (lastSignature.value === null) {
      lastSignature.value = signature
      console.log('[AutoReload] Baseline set:', signature)
      return false
    }

    if (signature !== lastSignature.value) {
      console.log('[AutoReload] Change detected:', lastSignature.value, '→', signature)
      lastSignature.value = signature
      return true
    }
    return false
  }

  /**
   * 変更を検知して画像リストをリロード
   */
  const checkForChanges = async () => {
    // 重複実行を防ぐ
    if (isChecking) return
    isChecking = true

    try {
      // ローディング中またはリロード中はスキップ
      if (eagleApi.isImagesLoading.value || isReloading.value) {
        console.log('[AutoReload] Skipped: images loading or reloading')
        return
      }

      const changed = await checkItemSignature()
      if (changed === true) {
        console.log('[AutoReload] Change detected via polling, reloading...')
        await reloadCurrentView()
      } else if (changed === null) {
        console.log('[AutoReload] Check skipped: API unreachable')
      }
    } finally {
      isChecking = false
    }
  }

  /**
   * 現在の表示を非破壊的にリロード（表示済みページ数分を再取得）
   */
  const reloadCurrentView = async () => {
    const currentFolderId = store.getCurrentFolderId
    if (!currentFolderId) return

    // Lightboxが開いている場合はリロードしない
    if (store.getCurrentImage) {
      console.log('[AutoReload] Skipping reload: Lightbox is open')
      return
    }

    isReloading.value = true

    // 現在のスクロール位置を記憶
    const scrollY = window.scrollY

    // 現在表示済みのページ数分を再取得
    const pageCount = Math.max(1, store.getCurrentPageCount)
    const totalLimit = pageCount * ITEM_GET_COUNT

    console.log('[AutoReload] Reloading images for folder:', currentFolderId, 'pages:', pageCount)

    try {
      const newImages = await eagleApi.loadImages({
        folderId: currentFolderId,
        limit: totalLimit,
        offset: 0,
      })

      store.setImages(newImages)
      store.resetCurrentPageCount()

      // ページカウントを復元
      const actualPages = Math.ceil(newImages.length / ITEM_GET_COUNT) || 1
      for (let i = 0; i < actualPages; i++) {
        store.addCurrentPageCount()
      }
      eagleApi.hasMoreItems.value = newImages.length >= totalLimit

      // スクロール位置を復元
      await nextTick()
      requestAnimationFrame(() => {
        window.scrollTo(0, Math.min(scrollY, document.body.scrollHeight))
      })
    } catch (error) {
      console.warn('[AutoReload] Error reloading view:', error)
    } finally {
      // IntersectionObserverの誤発火を防ぐため少し遅延して解除
      setTimeout(() => {
        isReloading.value = false
      }, 200)
    }
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

    // lastSignature が未設定の場合のみ基準値を設定
    if (lastSignature.value === null) {
      checkForChanges()
    }

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
   * シグネチャの基準値をリセット（フォルダ切替時に呼び出す）
   */
  const resetBaseline = () => {
    lastSignature.value = null
  }

  /**
   * タブ復帰時の処理（確認→条件付きリロード）
   */
  const handleVisibilityChange = async () => {
    // autoReload が OFF なら何もしない
    if (!settings.getAutoReload()) return

    // 再入ガード
    if (isHandlingVisibility) return
    isHandlingVisibility = true

    try {
      // 最新アイテムのシグネチャで変更を確認（API 1回のみ）
      const changed = await checkItemSignature()

      if (changed === true) {
        console.log('[AutoReload] Changes detected on tab return, reloading...')
        await reloadCurrentView()
      } else {
        console.log('[AutoReload] No changes detected on tab return')
      }

      // ポーリングを再開
      startPolling()
    } finally {
      isHandlingVisibility = false
    }
  }

  /**
   * デバウンス付きvisibilitychangeハンドラ
   * hidden → 即座にポーリング停止
   * visible → 300msデバウンス後に handleVisibilityChange 実行
   */
  const debouncedVisibilityHandler = () => {
    if (document.hidden) {
      // hidden は即時処理
      stopPolling()
      if (visibilityDebounceTimer) {
        clearTimeout(visibilityDebounceTimer)
        visibilityDebounceTimer = null
      }
      return
    }

    // visible はデバウンス（モバイルでの連続発火対策）
    if (visibilityDebounceTimer) {
      clearTimeout(visibilityDebounceTimer)
    }
    visibilityDebounceTimer = setTimeout(() => {
      visibilityDebounceTimer = null
      handleVisibilityChange()
    }, 300)
  }

  /**
   * visibilitychangeリスナーを登録（重複防止付き）
   */
  const setupVisibilityListener = () => {
    // 既存のリスナーがあれば除去
    removeVisibilityListener()

    visibilityHandler = debouncedVisibilityHandler
    document.addEventListener('visibilitychange', visibilityHandler)
  }

  /**
   * visibilitychangeリスナーを解除
   */
  const removeVisibilityListener = () => {
    if (visibilityHandler) {
      document.removeEventListener('visibilitychange', visibilityHandler)
      visibilityHandler = null
    }
    if (visibilityDebounceTimer) {
      clearTimeout(visibilityDebounceTimer)
      visibilityDebounceTimer = null
    }
  }

  return {
    isPolling,
    isReloading,
    startPolling,
    stopPolling,
    restartPolling,
    resetBaseline,
    checkForChanges,
    setupVisibilityListener,
    removeVisibilityListener,
  }
}

export function useAutoReload() {
  if (!instance) {
    instance = createAutoReload()
  }
  return instance
}
