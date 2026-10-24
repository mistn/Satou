/**
 * 在客户端应用初始化时根据 cookie 同步语言，避免 SSR 渲染语言与客户端不一致造成的闪烁。
 */
export default defineNuxtPlugin({
  name: 'i18n-cookie-sync',
  enforce: 'pre',
  setup(nuxtApp) {
    if (import.meta.server) return

    const cookie = useCookie('i18n_redirected')
    const i18n = nuxtApp.$i18n as unknown as { locale: string; setLocale: (l: string) => Promise<string> }

    if (cookie.value && cookie.value !== i18n.locale) {
      i18n.setLocale(cookie.value)
    }
  },
})
