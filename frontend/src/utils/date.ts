import dayjs from 'dayjs'

/** 格式化日期为 yyyy-MM-dd */
export function formatDate(date: Date | string | number | undefined | null): string {
  if (!date) return ''
  return dayjs(date).format('YYYY-MM-DD')
}

/** 格式化日期时间为 yyyy-MM-dd HH:mm */
export function formatDateTime(date: Date | string | number | undefined | null): string {
  if (!date) return ''
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

/** 格式化日期时间为 yyyy-MM-dd HH:mm:ss */
export function formatDateTimeFull(date: Date | string | number | undefined | null): string {
  if (!date) return ''
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

/** 相对时间（如 "3小时前"） */
export function fromNow(date: Date | string | number | undefined | null): string {
  if (!date) return ''
  const d = dayjs(date)
  const now = dayjs()
  const diffMinutes = now.diff(d, 'minute')
  if (diffMinutes < 1) return '刚刚'
  if (diffMinutes < 60) return `${diffMinutes}分钟前`
  const diffHours = now.diff(d, 'hour')
  if (diffHours < 24) return `${diffHours}小时前`
  const diffDays = now.diff(d, 'day')
  if (diffDays < 30) return `${diffDays}天前`
  return formatDate(date)
}
