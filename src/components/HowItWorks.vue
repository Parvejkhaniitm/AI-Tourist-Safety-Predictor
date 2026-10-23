<script setup>
const steps = ['Select Destination', 'Analyze Risk', 'Explore Safer Route']
</script>

<template>
  <section aria-labelledby="how-it-works-heading">
    <h2 id="how-it-works-heading" class="h6 fw-bold text-muted mb-3">How it works</h2>

    <div class="d-flex flex-column flex-md-row align-items-stretch gap-2">
      <template v-for="(step, index) in steps" :key="step">
        <div class="sr-step flex-fill d-flex align-items-center gap-3 px-3 py-3">
          <span class="step-number d-inline-flex align-items-center justify-content-center">
            {{ index + 1 }}
          </span>
          <span>{{ step }}</span>
        </div>

        <span
          v-if="index < steps.length - 1"
          class="d-none d-md-flex align-items-center fs-4 text-muted"
          aria-hidden="true"
        >
          &rarr;
        </span>
      </template>
    </div>
  </section>
</template>