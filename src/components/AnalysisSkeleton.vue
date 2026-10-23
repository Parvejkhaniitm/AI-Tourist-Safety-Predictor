<script setup>
defineProps({
  destination: { type: String, default: '' },
})
</script>

<template>
  <section aria-live="polite" aria-busy="true">
    <div class="d-flex align-items-center gap-3 mb-3">
      <div class="spinner-border spinner-border-sm" role="status">
        <span class="visually-hidden">Loading</span>
      </div>
      <span class="fs-5">Analyzing {{ destination }}...</span>
    </div>

    <div class="progress mb-4" style="height: 6px">
      <div class="progress-bar progress-bar-striped progress-bar-animated" style="width: 55%"></div>
    </div>

    <div class="row g-3 placeholder-glow">
      <div v-for="n in 3" :key="n" class="col-md-4">
        <div class="placeholder rounded w-100" style="height: 90px"></div>
      </div>
    </div>
  </section>
</template>