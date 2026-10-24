<template>
  <!--
    Single-screen hero. Layout mirrors public/preview.jpg (the OG card):
    portrait on the left, then name / tagline / quote stacked on the right,
    with the action pills underneath. Stacks vertically below `lg`.
  -->
  <header
    id="home"
    class="relative min-h-screen flex items-center justify-center px-6 py-24 overflow-hidden"
  >
    <!-- Soft colour wash behind the portrait -->
    <div
      class="hero-glow"
      aria-hidden="true"
    />

    <div class="relative z-10 w-full max-w-5xl mx-auto">
      <div class="flex flex-col lg:flex-row items-center justify-center gap-9 sm:gap-11 lg:gap-16">
        <div class="avatar-frame animate-fadeIn">
          <img
            src="/avatar.jpg"
            alt="松坂砂糖"
            width="512"
            height="512"
            class="avatar-img"
            fetchpriority="high"
            decoding="async"
          >
        </div>

        <div class="w-full lg:w-auto text-center lg:text-left">
          <h1
            class="hero-name animate-fadeInUp"
            :class="locale === 'zh' ? 'name-cjk' : 'hero-name--latin'"
            style="animation-delay: 0.15s"
          >
            {{ $t('hero.name') }}
          </h1>

          <p
            class="hero-subtitle animate-fadeInUp"
            style="animation-delay: 0.3s"
          >
            HAPPY SUGAR LIFE
          </p>

          <p
            class="hero-quote animate-fadeInUp"
            style="animation-delay: 0.45s"
          >
            Happiness is sweet - and it's all mine.
          </p>

          <div
            class="flex flex-wrap gap-2 sm:gap-3 items-center justify-center lg:justify-start animate-fadeInUp"
            style="animation-delay: 0.6s"
          >
            <!-- 语言切换 -->
            <button
              class="home !text-sm lg:!text-base"
              :aria-label="locale === 'en' ? 'Switch to Chinese' : 'Switch to English'"
              @click.prevent="toggleLocale"
            >
              <span class="tracking-wide">{{ locale === 'en' ? '中' : 'EN' }}</span>
            </button>

            <!-- 歌单入口 -->
            <NuxtLink
              to="/music"
              class="home !text-sm lg:!text-base"
              aria-label="Music"
            >
              Music
            </NuxtLink>

            <!-- 唯一联系入口 -->
            <button
              class="home !text-sm lg:!text-base"
              style="background: var(--text-primary); color: var(--color-black)"
              @click="openMail"
            >
              {{ $t('hero.get_in_touch') }}<span class="inline-block align-middle ml-2 group-hover:scale-125 transition-transform">
                <Icon
                  name="mingcute:mail-fill"
                  class="text-lg lg:text-xl -mt-1"
                  width="1em"
                  height="1em"
                />
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <TransitionDXTransition :loading="dxTransitionLoading" />
  </header>
</template>

<script setup>
import TransitionDXTransition from './Transition/DXTransition.vue'

const { locale, setLocale } = useI18n()

const dxTransitionLoading = ref(false)

function toggleLocale() {
  if (dxTransitionLoading.value) return
  const next = locale.value === 'zh' ? 'en' : 'zh'
  dxTransitionLoading.value = true
  setTimeout(() => {
    document.cookie = `i18n_redirected=${next};path=/;max-age=31536000;SameSite=Lax`
    setLocale(next)
  }, 400)
  setTimeout(() => {
    dxTransitionLoading.value = false
  }, 1200)
}

function openMail() {
  if (typeof window !== 'undefined' && typeof window.openMailClient === 'function') {
    window.openMailClient()
  }
}
</script>

<style scoped>
/* ── Ambient wash: pink on the portrait side, violet on the far side ────── */
.hero-glow {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(42% 42% at 24% 48%, rgb(238 114 178 / 0.14), transparent 70%),
    radial-gradient(55% 55% at 76% 60%, rgb(167 139 250 / 0.10), transparent 72%);
}

/* ── Portrait: rounded square with a thin light rim and a pink cast ─────── */
.avatar-frame {
  width: 9rem;
  height: 9rem;
  flex-shrink: 0;
  overflow: hidden;
  border-radius: 1.5rem;
  border: 2px solid rgb(255 255 255 / 0.5);
  background: rgb(255 255 255 / 0.04);
  box-shadow:
    0 22px 60px -18px rgb(238 114 178 / 0.55),
    0 0 0 1px rgb(0 0 0 / 0.25);
}

@media (min-width: 640px) {
  .avatar-frame {
    width: 11rem;
    height: 11rem;
    border-radius: 1.75rem;
  }
}

@media (min-width: 1024px) {
  .avatar-frame {
    width: 15rem;
    height: 15rem;
    border-radius: 2rem;
  }
}

.avatar-img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* ── Type scale, sampled from preview.jpg ──────────────────────────────── */
.hero-name {
  font-size: clamp(2.5rem, 6.5vw, 4.5rem);
  font-weight: 700;
  line-height: 1.12;
  /* .name-cjk sets 0.05em; display sizes read better slightly tighter */
  letter-spacing: 0.01em;
  color: #fcfcfc;
  margin-bottom: 1rem;
}

/* Latin name is 15 characters instead of 4 CJK glyphs, so it needs a smaller
   ceiling to stay on one line next to the portrait. */
.hero-name--latin {
  font-family: "Google Sans Flex", sans-serif;
  font-weight: 800;
  letter-spacing: -0.015em;
  font-size: clamp(2rem, 5vw, 3.25rem);
}

.hero-subtitle {
  font-size: clamp(0.8rem, 1.6vw, 1.0625rem);
  font-weight: 700;
  letter-spacing: 0.32em;
  color: #ee72b2;
  margin-bottom: 1.6rem;
}

.hero-quote {
  font-size: clamp(0.95rem, 1.8vw, 1.125rem);
  line-height: 1.7;
  color: #a8a8a8;
  margin-bottom: 2.5rem;
}
</style>
