<script setup lang="ts">
defineProps<{
  isPlaying: boolean
  currentTime: number
  duration: number
  progress: number
  volume: number
  isMuted: boolean
  shuffle: boolean
  repeat: 'none' | 'all' | 'one'
}>()

const emit = defineEmits<{
  prevTrack: []
  togglePlay: []
  nextTrack: []
  seek: [event: Event]
  setVolume: [event: Event]
  toggleMute: []
  toggleShuffle: []
  toggleRepeat: []
}>()

function formatTime(s: number) {
  if (!Number.isFinite(s) || s < 0) return '00:00'
  return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(Math.floor(s % 60)).padStart(2, '0')}`
}
</script>

<template>
  <div class="control-bar relative z-[3] flex-shrink-0 px-6 pt-[0.7rem] pb-[1.6rem] backdrop-blur-md max-sm:z-20 max-sm:px-3 max-sm:pt-2 max-sm:pb-3">
    <!-- Desktop: single row -->
    <div class="flex items-center gap-[0.3rem] max-sm:hidden">
      <button class="ctrl-btn" title="Previous" @click="emit('prevTrack')">
        <Icon name="mdi:skip-previous" />
      </button>
      <button
        class="ctrl-btn ctrl-btn--play"
        :title="isPlaying ? 'Pause' : 'Play'"
        @click="emit('togglePlay')"
      >
        <Icon :name="isPlaying ? 'mdi:pause' : 'mdi:play'" />
      </button>
      <button class="ctrl-btn" title="Next" @click="emit('nextTrack')">
        <Icon name="mdi:skip-next" />
      </button>

      <div class="flex-1 min-w-0 flex flex-col gap-[0.15rem]">
        <div class="progress-track">
          <div class="progress-fill" :style="{ width: `${progress * 100}%` }" />
          <div class="progress-thumb" :style="{ left: `${progress * 100}%` }" />
          <input
            type="range"
            class="progress-input"
            min="0"
            :max="duration || 100"
            step="0.1"
            :value="currentTime"
            @input="emit('seek', $event)"
          >
        </div>
      </div>

      <span
        class="flex-shrink-0 px-[0.35rem] text-[0.75rem] whitespace-nowrap tabular-nums"
        style="color: rgba(255,255,255,.75)"
      >
        {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
      </span>

      <div class="relative flex-shrink-0 flex items-center">
        <button
          class="ctrl-btn"
          :title="isMuted ? 'Unmute' : 'Mute'"
          @click="emit('toggleMute')"
        >
          <Icon :name="isMuted ? 'mdi:volume-off' : 'mdi:volume-high'" />
        </button>
        <div class="vol-track">
          <div class="vol-fill" :style="{ width: `${volume * 100}%` }" />
          <div class="vol-thumb" :style="{ left: `${volume * 100}%` }" />
          <input
            type="range"
            class="vol-input"
            min="0"
            max="1"
            step="0.01"
            :value="volume"
            @input="emit('setVolume', $event)"
          >
        </div>
      </div>

      <button
        class="ctrl-btn ml-3"
        :class="{ 'is-on': shuffle }"
        title="Shuffle"
        @click="emit('toggleShuffle')"
      >
        <Icon name="mdi:shuffle" />
      </button>
      <button
        class="ctrl-btn"
        :class="{ 'is-on': repeat !== 'none' }"
        :title="repeat === 'one' ? 'Repeat one' : repeat === 'all' ? 'Repeat all' : 'No repeat'"
        @click="emit('toggleRepeat')"
      >
        <Icon :name="repeat === 'one' ? 'mdi:repeat-once' : 'mdi:repeat'" />
      </button>
    </div>

    <!-- Mobile: two rows -->
    <div class="hidden max-sm:flex max-sm:flex-col max-sm:gap-2">
      <!-- Row 1: time + progress -->
      <div class="flex items-center gap-2">
        <span class="text-[0.65rem] whitespace-nowrap tabular-nums flex-shrink-0" style="color: rgba(255,255,255,.65)">
          {{ formatTime(currentTime) }}
        </span>
        <div class="flex-1 min-w-0">
          <div class="progress-track">
            <div class="progress-fill" :style="{ width: `${progress * 100}%` }" />
            <div class="progress-thumb" :style="{ left: `${progress * 100}%` }" />
            <input
              type="range"
              class="progress-input"
              min="0"
              :max="duration || 100"
              step="0.1"
              :value="currentTime"
              @input="emit('seek', $event)"
            >
          </div>
        </div>
        <span class="text-[0.65rem] whitespace-nowrap tabular-nums flex-shrink-0" style="color: rgba(255,255,255,.65)">
          {{ formatTime(duration) }}
        </span>
      </div>
      <!-- Row 2: controls -->
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-1">
          <button class="ctrl-btn" title="Previous" @click="emit('prevTrack')">
            <Icon name="mdi:skip-previous" />
          </button>
          <button
            class="ctrl-btn ctrl-btn--play"
            :title="isPlaying ? 'Pause' : 'Play'"
            @click="emit('togglePlay')"
          >
            <Icon :name="isPlaying ? 'mdi:pause' : 'mdi:play'" />
          </button>
          <button class="ctrl-btn" title="Next" @click="emit('nextTrack')">
            <Icon name="mdi:skip-next" />
          </button>
        </div>
        <div class="flex items-center gap-1">
          <button
            class="ctrl-btn"
            :class="{ 'is-on': shuffle }"
            title="Shuffle"
            @click="emit('toggleShuffle')"
          >
            <Icon name="mdi:shuffle" />
          </button>
          <button
            class="ctrl-btn"
            :class="{ 'is-on': repeat !== 'none' }"
            :title="repeat === 'one' ? 'Repeat one' : repeat === 'all' ? 'No repeat' : 'Repeat all'"
            @click="emit('toggleRepeat')"
          >
            <Icon :name="repeat === 'one' ? 'mdi:repeat-once' : 'mdi:repeat'" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes bar-slide-in {
  from {
    opacity: 0;
    transform: translateY(2.5rem);
  }
}

.control-bar {
  animation: bar-slide-in 450ms cubic-bezier(0.1, 0.9, 0.2, 1) 600ms backwards;
}

/* Custom slider track overlay pattern — requires absolute positioning + transparent input */
.progress-track,
.vol-track {
  position: relative;
  height: 4px;
  background: rgba(255,255,255,.18);
  border-radius: 2px;
  cursor: pointer;
}

.progress-track { width: 100%; }
.vol-track { width: 80px; flex-shrink: 0; }

.progress-fill,
.vol-fill {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  background: rgba(255,255,255,.85);
  border-radius: 2px;
  pointer-events: none;
  transition: width .1s linear;
}

.progress-thumb,
.vol-thumb {
  position: absolute;
  top: 50%;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #fff;
  transform: translate(-50%, -50%);
  pointer-events: none;
  box-shadow: 0 1px 4px rgba(0,0,0,.4);
  transition: left .1s linear;
}

.progress-input,
.vol-input {
  position: absolute;
  inset: -8px 0;
  opacity: 0;
  width: 100%;
  cursor: pointer;
  height: calc(100% + 16px);
}

.ctrl-btn {
  width: 38px;
  height: 38px;
  flex-shrink: 0;
  border-radius: 50%;
  background: none;
  border: none;
  color: rgba(255,255,255,.7);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.45rem;
  transition: color .15s, background .15s;
}

@media (max-width: 640px) {
  .ctrl-btn { width: 32px; height: 32px; font-size: 1.2rem; }
  .ctrl-btn--play { width: 40px; height: 40px; font-size: 1.35rem; }
}

@media (hover: hover) {
  .ctrl-btn:hover {
    color: #fff;
    background: rgba(255,255,255,.09);
  }
}

.ctrl-btn.is-on {
  color: #fff;
  background: rgba(255,255,255,.15);
}

.ctrl-btn--play {
  width: 46px;
  height: 46px;
  background: rgba(255,255,255,.14);
  font-size: 1.6rem;
}

@media (hover: hover) {
  .ctrl-btn--play:hover { background: rgba(255,255,255,.22); }
}
</style>
