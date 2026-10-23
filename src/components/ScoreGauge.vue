<script setup>
import { computed } from 'vue'
import { getRiskLevel } from '../utils/risk'

const props = defineProps({
  score: { type: Number, default: null },
})

// Circle ki geometry: circumference = 2 * pi * radius
const RADIUS = 52
const CIRCUMFERENCE = 2 * Math.PI * RADIUS

// Score ko 0-100 ke beech rakho (galat value aaye to bhi gauge na toote)
const position = computed(() =>
  props.score === null ? 0 : Math.min(100, Math.max(0, props.score)),
)
const risk = computed(() => getRiskLevel(props.score))

// Jitna risk score zyada, utna circle ka zyada hissa bhara hua
const dashOffset = computed(() => CIRCUMFERENCE * (1 - position.value / 100))
</script>

<template>
  <div>
    <div class="gauge-circle">
      <svg viewBox="0 0 120 120" role="img" :aria-label="`Risk score ${score ?? 'not available'} out of 100`">
        <circle class="gauge-track" cx="60" cy="60" :r="RADIUS" />
        <circle
          class="gauge-value"
          :class="`gauge-${risk.variant}`"
          cx="60"
          cy="60"
          :r="RADIUS"
          :stroke-dasharray="CIRCUMFERENCE"
          :stroke-dashoffset="dashOffset"
          transform="rotate(-90 60 60)"
        />
      </svg>
      <div class="gauge-text">
        <span class="gauge-number">{{ score ?? '--' }}</span>
        <span class="gauge-caption">risk score / 100</span>
      </div>
    </div>

    <div class="score-scale">
      <div class="scale-track">
        <div class="scale-bar">
          <span class="seg-safe" style="width: 40%"></span>
          <span class="seg-moderate" style="width: 30%"></span>
          <span class="seg-high" style="width: 30%"></span>
        </div>
        <span v-if="score !== null" class="scale-marker" :style="{ left: `${position}%` }"></span>
      </div>
      <div class="scale-labels">
        <span style="width: 40%">Safe 0-39</span>
        <span style="width: 30%">Moderate 40-69</span>
        <span style="width: 30%">High Risk 70-100</span>
      </div>
    </div>
  </div>
</template>