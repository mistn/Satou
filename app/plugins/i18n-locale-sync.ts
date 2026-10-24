/**
 * 纯静态站没有运行时 SSR，语言恢复只能在客户端做：
 * 按 cookie 把语言切回上次使用的值，且必须在 i18n 初始化之后、首屏渲染之前执行。
 * 注意：不能加 enforce: 'pre' —— 那会排到 @nuxtjs/i18n 提供 $i18n 的插件之前，
 * $i18n 还是 undefined，带 cookie 的访客会直接 500（e3e6843 的教训）。
 */
export default defineNuxtPlugin({
  name: 'i18n-locale-sync',
  setup(nuxtApp) {
    if (import.meta.server) return

    const cookie = useCookie('i18n_redirected')
    const i18n = nuxtApp.$i18n as unknown as
      | { locale: string, setLocale: (locale: string) => Promise<unknown> }
      | undefined

    if (cookie.value && i18n && cookie.value !== i18n.locale) {
      // 消息包加载失败时保持当前语言即可，不能让未捕获的拒绝冒泡成 500
      i18n.setLocale(cookie.value).catch(() => {})
    }
  },
})
