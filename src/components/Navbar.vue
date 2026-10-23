<script setup>
// Main journeys plus a direct planning action.
const links = [
  { label: 'Home', to: '/' },
  { label: 'Check Safety', to: '/analysis' },
  { label: 'About', to: '/about' },
]
</script>

<template>
  <nav class="navbar navbar-expand-md sr-navbar py-3" aria-label="Main navigation">
    <div class="container">
      <RouterLink class="navbar-brand fw-bold d-flex align-items-center gap-2" to="/">
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path d="M12 3l7 3v5c0 5-3 8-7 10-4-2-7-5-7-10V6l7-3z" />
          <path d="M9 12l2 2 4-4" />
        </svg>
        SafeRoute AI
      </RouterLink>

      <button
        class="navbar-toggler"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#mainNavbar"
        aria-controls="mainNavbar"
        aria-expanded="false"
        aria-label="Toggle navigation"
      >
        <span class="navbar-toggler-icon"></span>
      </button>

      <div class="collapse navbar-collapse" id="mainNavbar">
        <ul class="navbar-nav ms-auto align-items-md-center gap-md-2 mb-2 mb-md-0">
          <li v-for="link in links" :key="link.to" class="nav-item">
            <RouterLink class="nav-link" :to="link.to" exact-active-class="active">
              {{ link.label }}
            </RouterLink>
          </li>
          <li class="nav-item ms-md-2">
            <RouterLink class="btn btn-primary" to="/analysis">Start planning <span aria-hidden="true">↗</span></RouterLink>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>
