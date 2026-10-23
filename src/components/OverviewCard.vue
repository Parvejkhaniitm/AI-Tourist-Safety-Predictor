<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: String, default: '--' },
  hint: { type: String, default: '' },
  muted: { type: Boolean, default: false },   // true = grey (empty state)
  compact: { type: Boolean, default: false }, // chhota font (lambi date ke liye)
})
</script>

<template>
  <div
    class="sr-card-dashed h-100 p-3 d-flex flex-row flex-md-column justify-content-between justify-content-md-start align-items-center align-items-md-start"
  >
    <p class="fw-semibold small mb-md-1 mb-0">{{ label }}</p>

    <div class="sr-value" :class="{ 'text-faint': muted, compact: compact }">
      <slot>{{ value }}</slot>
    </div>

    <p v-if="hint" class="text-muted small mb-0 mt-md-1 d-none d-md-block">{{ hint }}</p>
  </div>
</template>