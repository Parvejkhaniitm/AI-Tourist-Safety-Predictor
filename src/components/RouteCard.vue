<script setup>
import { computed } from 'vue'
import RiskBadge from './RiskBadge.vue'
import { getRiskLevel } from '../utils/risk'

const props = defineProps({
  label: { type: String, required: true },
  distanceKm: { type: Number, required: true },
  durationMin: { type: Number, required: true },
  score: { type: Number, required: true },
  note: { type: String, default: '' },
  recommended: { type: Boolean, default: false },
  variant: { type: String, default: 'shortest' }, // 'shortest' ya 'safer' (dot ka rang)
})

// Score ke hisaab se progress bar ka rang: bar-safe / bar-moderate / bar-high
const barClass = computed(() => `bar-${getRiskLevel(props.score).variant}`)
</script>

<template>
  <article class="sr-card route-card h-100 p-4" :class="{ 'route-card-recommended': recommended }">
    <div class="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
      <h3 class="h5 fw-bold mb-0 d-flex align-items-center gap-2">
        <span class="dot" :class="`dot-${variant}`" aria-hidden="true"></span>
        {{ label }}
      </h3>
      <div class="d-flex align-items-center gap-2">
        <span v-if="recommended" class="recommended-pill">Recommended</span>
        <RiskBadge :score="score" />
      </div>
    </div>

    <div class="row g-3 mb-3">
      <div class="col-6">
        <div class="route-stat-value">{{ distanceKm }} km</div>
        <div class="small text-muted">distance</div>
      </div>
      <div class="col-6">
        <div class="route-stat-value">{{ durationMin }} min</div>
        <div class="small text-muted">estimated</div>
      </div>
    </div>

    <div class="d-flex justify-content-between small fw-semibold mb-1">
      <span>Route safety score</span>
      <span>{{ score }} / 100</span>
    </div>
    <div
      class="progress mb-3"
      style="height: 8px"
      role="progressbar"
      :aria-label="`${label} safety score`"
      :aria-valuenow="score"
      aria-valuemin="0"
      aria-valuemax="100"
    >
      <div class="progress-bar" :class="barClass" :style="{ width: `${score}%` }"></div>
    </div>

    <p v-if="note" class="small text-muted mb-0">{{ note }}</p>
  </article>
</template>