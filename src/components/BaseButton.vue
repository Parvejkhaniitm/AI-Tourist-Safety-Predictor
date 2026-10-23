<script setup>
import { computed } from 'vue'

// defineProps: parent se aane wale inputs declare karta hai.
const props = defineProps({
  variant: { type: String, default: 'primary' }, // primary, secondary, success, danger...
  outline: { type: Boolean, default: false },
  size: { type: String, default: '' },           // '' (normal), 'sm', 'lg'
  type: { type: String, default: 'button' },     // 'button' ya 'submit'
  disabled: { type: Boolean, default: false },
})

// computed: props badalte hi classes khud dubara calculate hoti hain.
const classes = computed(() => [
  'btn',
  props.outline ? `btn-outline-${props.variant}` : `btn-${props.variant}`,
  props.size ? `btn-${props.size}` : '',
])
</script>

<template>
  <button :type="type" :class="classes" :disabled="disabled">
    <slot />
  </button>
</template>