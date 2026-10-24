/** Audio container the CDN (or local folder) holds for a track. `mp3` is the default when unspecified. */
type AudioFormat = 'mp3' | 'flac'

interface SongConfig {
  name: string
  artist: string
  /**
   * Folder / file name under `cdnUrl`. Defaults to a slug derived from `name`.
   * Set this explicitly when the derived slug would contain non-ASCII characters.
   */
  slug?: string
  /** Audio container extension, e.g. `"flac"`. Falls back to `"mp3"`. */
  format?: string
  /** `true` when `<slug>.webp` sits next to the audio file. Omit otherwise. */
  cover?: boolean
  /** `true` when `<slug>.lrc` sits next to the audio file. Omit otherwise. */
  lrc?: boolean
}

interface MusicConfig {
  cdnUrl: string
  songs: SongConfig[]
}

/** Containers every modern browser can play directly. Anything else falls back to mp3. */
const PLAYABLE_EXTENSIONS = new Set(['mp3', 'flac', 'm4a', 'wav', 'ogg', 'opus'])

function resolveFormat(format?: string): string {
  const normalized = format?.trim().toLowerCase().replace(/^\./, '')
  return normalized && PLAYABLE_EXTENSIONS.has(normalized) ? normalized : 'mp3'
}

function normalizeName(name: string): string {
  return name
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[ \t_`~!@#$%^&*()[\]{}|\\;:'",./<>?+\-=]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

export default defineEventHandler(async () => {
  const storage = useStorage('assets:server')
  const data = await storage.getItem<MusicConfig>('music.json')
  if (!data || !Array.isArray(data.songs)) return []

  // `cdnUrl` may be an absolute CDN origin or a site-relative folder such as `/music/`.
  const base = data.cdnUrl.endsWith('/') ? data.cdnUrl : data.cdnUrl + '/'

  return data.songs.map((song) => {
    const { name, artist, format, slug, cover, lrc } = song
    const dir = slug?.trim() || normalizeName(name)
    const audioFormat = resolveFormat(format)
    const file = encodeURIComponent(dir)

    return {
      name,
      artist,
      format: audioFormat,
      url: `${base}${file}/${file}.${audioFormat}`,
      // Empty strings keep the player's built-in empty-cover / no-lyrics states working.
      cover: cover ? `${base}${file}/${file}.webp` : '',
      lrc: lrc ? `${base}${file}/${file}.lrc` : '',
    }
  })
})
