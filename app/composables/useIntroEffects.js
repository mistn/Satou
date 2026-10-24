import { onMounted } from 'vue'

/**
 * Page-level side effects for the single-screen homepage.
 *
 * The scroll-driven logic that used to live here (hero fade, scroll spy,
 * back-to-top, footer hover tints) was removed together with the sections
 * it drove — the page no longer scrolls, so every branch was a no-op.
 */
export function useIntroEffects() {

  // ── Console status badge ───────────────────────────────────────────────────
  const logStatus = (message, { isError = false } = {}) => {
    const rootStyles = getComputedStyle(document.documentElement)
    const accentColor = isError
      ? '#ef4444'
      : (rootStyles.getPropertyValue('--accent-tertiary').trim() || '#a78bfa')

    const getRgba = (hex) => {
      const cleanHex = hex.replace('#', '')
      const r = parseInt(cleanHex.substring(0, 2), 16)
      const g = parseInt(cleanHex.substring(2, 4), 16)
      const b = parseInt(cleanHex.substring(4, 6), 16)
      return `rgba(${r}, ${g}, ${b}, 0.15)`
    }

    const rightBg = getRgba(accentColor)

    console.log(
      `%cdp.Intro %c ${message} `,
      `color: white; font-weight: bold; border-radius: 3px 0 0 3px; padding: 2px 4px 1px 10px; background: ${accentColor}`,
      `color: white; border-radius: 0 3px 3px 0; padding: 2px 10px 1px 4px; background: ${rightBg}`,
      ''
    )
  }

  /**
   * 使用多行字符串并在控制台打印渐变色
   * @param {string} charString - 多行字符串
   * @param {string} startColor - 起始颜色 (rgb)
   * @param {string} endColor - 结束颜色 (rgb)
   */
  function printGradientString(charString, startColor, endColor) {
    const parseRGB = (str) => str.match(/\d+/g).map(Number)
    const s = parseRGB(startColor)
    const e = parseRGB(endColor)

    const lines = charString.split('\n')
    let fullOutput = ''

    lines.forEach((line) => {
      if (line.length === 0) return

      const chars = [...line]
      const rowLength = chars.length

      chars.forEach((char, index) => {
        const ratio = rowLength > 1 ? index / (rowLength - 1) : 0

        const r = Math.round(s[0] + (e[0] - s[0]) * ratio)
        const g = Math.round(s[1] + (e[1] - s[1]) * ratio)
        const b = Math.round(s[2] + (e[2] - s[2]) * ratio)

        fullOutput += `\x1b[38;2;${r};${g};${b}m${char}`
      })

      fullOutput += '\x1b[0m\n'
    })

    console.log(fullOutput)
  }

  const art = String.raw`

 松坂砂糖  ·  Satou

 © 2026 松坂砂糖. Happiness is sweet - and it's all mine.

`

  onMounted(() => {
    const startTime = performance.now()

    // ── Expose `openMailClient` globally for inline onclick handlers ──
    window.openMailClient = function openMailClient() {
      const email = 'Satou@wav.im'
      window.location.href = `mailto:${email}`
    }
    window.lazyLoadOptions = {
      threshold: 400,
      cancel_on_exit: false
    }

    logStatus('Initializing...')
    printGradientString(art, 'rgb(192, 106, 217)', 'rgb(54, 38, 173)')

    try {
      logStatus(`Loaded successfully! Cost ${(performance.now() - startTime).toFixed(1)}ms`)
    } catch (err) {
      logStatus(`Error: ${err.message}`, { isError: true })
      console.error(err.stack)
    }
  })
}
