import { onUnmounted, ref } from 'vue'

/**
 * 请求取消 Composable — 组件卸载时自动取消未完成的请求
 * 返回 cancel 函数和重建 AbortController 的函数
 */
export function useRequestCancel() {
  const controller = ref<AbortController>(new AbortController())

  function getSignal(): AbortSignal {
    return controller.value.signal
  }

  function resetController() {
    controller.value = new AbortController()
    return controller.value.signal
  }

  function cancelAll() {
    controller.value.abort()
  }

  onUnmounted(() => {
    cancelAll()
  })

  return { getSignal, resetController, cancelAll }
}
