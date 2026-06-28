/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// 注意：不再声明 @/api 为 any，让 TypeScript 从 src/api/index.ts 自动推断类型
// 各 API 函数应在 src/api/index.ts 中显式声明入参与返回值类型
