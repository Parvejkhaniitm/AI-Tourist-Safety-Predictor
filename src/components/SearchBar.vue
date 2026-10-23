<script setup>
import { ref } from 'vue'
import { reverseGeocodeCoordinates } from '../services/api'

defineProps({
  modelValue: { type: String, default: '' },
  start: { type: String, default: '' },
  suggestions: { type: Array, default: () => [] },
  error: { type: String, default: '' },
  startError: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'update:start', 'update:startCoordinates', 'submit'])

const locating = ref(false)
const locationMsg = ref('')

function onInput(event) {
  emit('update:modelValue', event.target.value)
}

function onStartInput(event) {
  emit('update:startCoordinates', null)
  emit('update:start', event.target.value)
}

// The explicit name lookup sends only rounded coordinates to the backend.
function useMyLocation() {
  if (!navigator.geolocation) {
    locationMsg.value = 'Your browser does not support location.'
    return
  }
  locating.value = true
  locationMsg.value = ''

  navigator.geolocation.getCurrentPosition(
    async (pos) => {
      const { latitude, longitude } = pos.coords
      const coordinates = { lat: latitude, lng: longitude }
      emit('update:startCoordinates', coordinates)
      emit('update:start', 'Finding your nearby area…')
      try {
        const placeName = await reverseGeocodeCoordinates(coordinates)
        emit('update:start', placeName ? `${placeName} · Current location` : `Current location (${latitude.toFixed(4)}, ${longitude.toFixed(4)})`)
        locationMsg.value = placeName ? `Location selected: ${placeName}` : 'Area name unavailable; your coordinates are still selected.'
      } catch {
        emit('update:start', `Current location (${latitude.toFixed(4)}, ${longitude.toFixed(4)})`)
        locationMsg.value = 'Area name unavailable; your coordinates are still selected.'
      } finally {
        locating.value = false
      }
    },
    () => {
      locating.value = false
      locationMsg.value = 'Location not allowed. Please type your starting point.'
    },
    { timeout: 10000 },
  )
}

</script>

<template>
  <form class="text-start" novalidate @submit.prevent="emit('submit')">
    <!-- Starting point -->
    <div class="mb-3">
      <label for="start-input" class="form-label fw-semibold small mb-1">Starting point</label>
      <input
        id="start-input"
        type="text"
        class="form-control form-control-lg"
        :class="{ 'is-invalid': startError }"
        :value="start"
        placeholder="Where are you starting from?"
        autocomplete="off"
        :aria-invalid="startError ? 'true' : 'false'"
        :aria-describedby="startError ? 'start-feedback' : null"
        @input="onStartInput"
      />
      <div v-if="startError" id="start-feedback" class="invalid-feedback">{{ startError }}</div>
    </div>

    <div class="d-flex flex-wrap align-items-center gap-2 mt-2">
      <button type="button" class="chip" :disabled="locating" @click="useMyLocation">
        {{ locating ? 'Finding nearby place…' : 'Use my location' }}
      </button>
      <span v-if="locationMsg" class="text-muted small">{{ locationMsg }}</span>
      <span v-else class="text-muted small">Area naming uses a rounded location with OpenStreetMap.</span>
    </div>

    <div class="search-grid">
      <label for="destination-input" class="sg-label form-label fw-semibold small mb-0">
        Destination
      </label>

      <div class="sg-field position-relative">
        <svg
          class="search-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          aria-hidden="true"
        >
          <circle cx="11" cy="11" r="7" />
          <path d="M20 20l-3.5-3.5" />
        </svg>

        <input
          id="destination-input"
          type="text"
          class="form-control form-control-lg search-input"
          :class="{ 'is-invalid': error }"
          :value="modelValue"
          list="destination-options"
          placeholder="Enter a city or tourist destination"
          autocomplete="off"
          :aria-invalid="error ? 'true' : 'false'"
          :aria-describedby="error ? 'destination-feedback' : null"
          @input="onInput"
        />
        <datalist id="destination-options">
          <option v-for="place in suggestions" :key="place" :value="place" />
        </datalist>

        <div v-if="error" id="destination-feedback" class="invalid-feedback">{{ error }}</div>
      </div>

      <div class="sg-chips d-flex flex-wrap gap-2 align-items-center justify-content-md-center">
        <span class="text-muted small">Try:</span>
        <button
          v-for="(place, index) in suggestions"
          :key="place"
          type="button"
          class="chip"
          :class="{ 'd-none d-md-inline-block': index > 2 }"
          @click="emit('update:modelValue', place)"
        >
          {{ place }}
        </button>
      </div>

      <button type="submit" class="sg-submit btn btn-primary btn-lg px-4">Analyze Risk</button>
    </div>

    <p class="text-center text-muted small mt-3 mb-0 d-none d-md-block">
      Search runs only when you press Analyze; suggestions are quick starts, not a required list.
    </p>
  </form>
</template>
