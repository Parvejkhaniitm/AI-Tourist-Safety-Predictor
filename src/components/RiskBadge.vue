<script setup>
import { computed } from 'vue'
import { getRiskLevel } from '../utils/risk'

const props = defineProps({
  score: { type: Number, default: null },
})

const risk = computed(() => getRiskLevel(props.score))
</script>

<template>
  <span class="badge fs-6 risk-badge" :class="`risk-badge-${risk.variant}`">
    {{ risk.label }}
  </span>
</template>

<style scoped>
.risk-badge{font-weight:800;letter-spacing:.01em;padding:.5em .75em}
.risk-badge-safe{color:#125a38!important;background:#d8f3e3!important;border:1px solid #8fd4ad}
.risk-badge-moderate{color:#704500!important;background:#fff0c2!important;border:1px solid #edc75e}
.risk-badge-high{color:#872b2b!important;background:#ffe0dc!important;border:1px solid #e8a29a}
.risk-badge-none{color:#425466!important;background:#e8edf2!important;border:1px solid #cbd5e1}
</style>
