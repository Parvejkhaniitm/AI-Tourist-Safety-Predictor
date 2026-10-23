<script setup>
import { computed } from 'vue'

const props = defineProps({
  type: { type: String, default: 'info' }, // info, success, warning, danger
  title: { type: String, default: '' },
})

const role = computed(() =>
  props.type === 'danger' || props.type === 'warning' ? 'alert' : 'status',
)
</script>

<template>
  <div class="status-message" :class="`status-${type}`" :role="role">
    <p v-if="title" class="fw-bold mb-1">{{ title }}</p>
    <slot />
  </div>
</template>