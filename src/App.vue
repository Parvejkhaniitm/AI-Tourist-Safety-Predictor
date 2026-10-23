<script setup>
import MainLayout from './layouts/MainLayout.vue'
</script>

<template>
  <MainLayout>
    <RouterView v-slot="{ Component, route }">
      <Transition name="page" mode="out-in">
        <component :is="Component" :key="route.name" />
      </Transition>
    </RouterView>
  </MainLayout>
</template>
