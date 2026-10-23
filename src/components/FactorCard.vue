<script setup>
defineProps({
  title: { type: String, required: true },
  text: { type: String, default: '' },
  impact: { type: String, default: 'neutral' }, // lowers | neutral | raises
  impactLabel: { type: String, default: '' },
  dataLabel: { type: String, default: '' },
  available: { type: Boolean, default: true },
  displayOnly: { type: Boolean, default: false },
})
</script>

<template>
  <article class="h-100 p-3 d-flex flex-column" :class="displayOnly || available ? 'sr-card' : 'sr-card-dashed'">
    <h3 class="h6 fw-bold mb-2">{{ title }}</h3>
    <p class="small text-muted flex-grow-1 mb-2">{{ text }}</p>

    <p v-if="!displayOnly && available" class="small fw-bold mb-1" :class="`impact-${impact}`">{{ impactLabel }}</p>
    <p v-else-if="!displayOnly" class="small fw-bold mb-1 text-muted">Data unavailable</p>

    <p v-if="dataLabel" class="small text-faint mb-0">{{ dataLabel }}</p>
  </article>
</template>
