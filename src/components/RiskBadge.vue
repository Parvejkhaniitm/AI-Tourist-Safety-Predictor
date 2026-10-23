<script setup>
import { computed } from 'vue'
import { getRiskLevel } from '../utils/risk'

const props = defineProps({
  score: { type: Number, default: null },
})

const risk = computed(() => getRiskLevel(props.score))
</script>

<template>
  <span class="badge fs-6" :class="`text-bg-${risk.variant}`">
    {{ risk.label }}
  </span>
</template>