<script setup>
import NavBar from '../components/NavBar.vue'
</script>

<template>
  <div class="d-flex flex-column min-vh-100">
    <NavBar />

    <main class="flex-grow-1">
      <slot />
    </main>

    <footer class="site-footer py-3 mt-auto">
      <div class="container d-flex flex-wrap justify-content-between gap-2 small">
        <span>SafeRoute AI · Plan with context. Travel with care.</span>
        <span>Demo estimates are not verified and do not guarantee personal safety.</span>
      </div>
    </footer>
  </div>
</template>
