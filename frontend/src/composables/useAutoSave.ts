/** 自动保存草稿 composable — 将表单状态防抖同步到 localStorage */
import { ref, watch, type Ref } from 'vue'

export function useAutoSave<T extends Record<string, unknown>>(
  key: string,
  data: Ref<T>,
  debounceMs = 2000,
) {
  const isRestored = ref(false)
  let timer: ReturnType<typeof setTimeout> | null = null

  // 恢复草稿
  const restore = (): T | null => {
    try {
      const raw = localStorage.getItem(`draft:${key}`)
      if (raw) {
        const parsed = JSON.parse(raw) as T
        isRestored.value = true
        return parsed
      }
    } catch {
      // ignore
    }
    return null
  }

  // 清除草稿
  const clear = () => {
    localStorage.removeItem(`draft:${key}`)
  }

  // 防抖保存
  watch(data, () => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      try {
        localStorage.setItem(`draft:${key}`, JSON.stringify(data.value))
      } catch {
        // quota exceeded, ignore
      }
    }, debounceMs)
  }, { deep: true })

  return { restore, clear, isRestored }
}
