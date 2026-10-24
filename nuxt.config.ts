// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  nitro: {
    // 纯静态站点：所有路由都在构建时预渲染，不需要 Cloudflare Worker
    preset: 'cloudflare-pages-static',
  },

  modules: [
    '@nuxtjs/tailwindcss',
    '@nuxtjs/i18n',
    '@nuxtjs/sitemap',
    '@nuxt/eslint',
    '@nuxt/icon',
    '@vueuse/nuxt'
  ],

  routeRules: {
    '/': { prerender: true },
    // 歌单和音频都在构建时确定，直接预渲染成静态页，不需要 Worker
    '/music': { prerender: true },
    // 音频和封面体积大、文件名随内容变，让浏览器长缓存。
    // Nitro 会把 /** 自动改写成 /* 再写进 _headers。
    '/music/**': { headers: { 'cache-control': 'public, max-age=2592000' } },
  },

  icon: {
    clientBundle: {
      scan: true,
    },
    mode: 'svg'
  },

  tailwindcss: {
    configPath: 'tailwind.config.js',
  },

  css: [
    '~/assets/css/main.css'
  ],

  postcss: {
    plugins: {
      tailwindcss: {},
      autoprefixer: {}
    }
  },

  site: {
    url: "https://wav.im",
    name: "松坂砂糖 — Intro"
  },

  sitemap: {
    zeroRuntime: true
  },

  app: {
    pageTransition: { name: 'page', mode: 'out-in' },
    head: {
      htmlAttrs: { lang: 'en' },
      title: '松坂砂糖',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1.0' },
        { name: 'description', content: "松坂砂糖 · Happiness is sweet, and it's all mine." },
        { name: 'author', content: 'satou' },
        { name: 'keywords', content: '松坂砂糖, satou, developer, technology, coding' },
        { name: 'robots', content: 'index, follow' },
        // If you're planning to deploy your own website, don't forget to replace this!
 
        // Open Graph / Facebook
        { property: 'og:type', content: 'website' },
        { property: 'og:title', content: "松坂砂糖" },
        { property: 'og:description', content: "松坂砂糖 · Happiness is sweet, and it's all mine." },
        { property: 'og:image', content: 'https://wav.im/preview.jpg' },
 
        // Twitter
        { name: 'twitter:card', content: 'summary_large_image' },
        { name: 'twitter:title', content: "松坂砂糖" },
        { name: 'twitter:description', content: "松坂砂糖 · Happiness is sweet, and it's all mine." },
        { name: 'twitter:image', content: 'https://wav.im/preview.jpg' }
      ],
      link: [
        { rel: 'icon', href: '/icon.jpg', type: 'image/jpeg' },
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=Google+Sans+Code:ital,wght@0,300..800;1,300..800&family=Google+Sans+Flex:opsz,wght@6..144,1..1000&display=swap&font-display=block'
        },
        {
          // 名字用的日文字体：text= 只子集「松坂砂糖」四个字，约 1.5KB
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=Zen+Kaku+Gothic+New:wght@700;900&text=%E6%9D%BE%E5%9D%82%E7%A0%82%E7%B3%96&display=swap'
        }
      ],
    }
  },

  i18n: {
    baseUrl: 'https://wav.im',
    strategy: 'no_prefix',
    defaultLocale: 'en',
    locales: [
      {
        code: 'en',
        name: 'English',
        file: 'en.json'
      },
      {
        code: 'zh',
        name: '简体中文',
        file: 'zh.json'
      }
    ],
    langDir: 'locales/',
    detectBrowserLanguage: {
      useCookie: true,
      cookieKey: 'i18n_redirected',
      alwaysRedirect: false,
      fallbackLocale: 'en',
    },
    experimental: {
      strictSeo: true
    }
  }
})
