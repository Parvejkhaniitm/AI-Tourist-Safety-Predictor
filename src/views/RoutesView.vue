<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import BaseButton from '../components/BaseButton.vue'
import StatusMessage from '../components/StatusMessage.vue'
import RouteCard from '../components/RouteCard.vue'
import RouteMap from '../components/RouteMap.vue'
import { fetchRoutes } from '../services/api'
import { destinationSuggestions } from '../data/mockDestinations'
import { getTradeOff, getRecommendedRoute, formatSigned } from '../utils/routes'

const route = useRoute()
const router = useRouter()

// --- State: idle | loading | success | error ---
const status = ref('idle')
const data = ref(null)
const errorInfo = ref(null)

const destinationName = computed(() => String(route.query.destination ?? '').trim())
const startName = computed(() => String(route.query.start ?? '').trim())


async function loadRoutes() {
  if (!destinationName.value) {
    status.value = 'idle'
    data.value = null
    return
  }

  const requested = destinationName.value
  status.value = 'loading'
  errorInfo.value = null

  try {
    const result = await fetchRoutes(requested, startName.value)
    if (requested !== destinationName.value) return // beech me destination badal gaya
    data.value = result
    status.value = 'success'
  } catch (err) {
    if (requested !== destinationName.value) return
    data.value = null
    errorInfo.value = { code: err.code ?? 'UNKNOWN', message: err.message || 'Something went wrong.' }
    status.value = 'error'
  }
}

watch(destinationName, loadRoutes, { immediate: true })

// --- Navigation ---
function goHome() {
  router.push({ name: 'home' })
}

function backToAnalysis() {
  router.push({
    name: 'analysis',
    query: { destination: data.value.destination, ...(startName.value && { start: startName.value }) },
  })
}
function tryDestination(place) {
  router.push({
    name: 'routes',
    query: { destination: place, ...(startName.value && { start: startName.value }) },
  })
}

// --- Derived values (saara hisaab utils/routes.js me hai) ---
const hasSafer = computed(() => !!data.value?.safer)

const recommendedKey = computed(() =>
  data.value ? getRecommendedRoute(data.value.shortest, data.value.safer) : null,
)
const saferRecommended = computed(() => hasSafer.value && recommendedKey.value === 'safer')
const shortestRecommended = computed(() => hasSafer.value && recommendedKey.value === 'shortest')

const tradeOff = computed(() =>
  hasSafer.value ? getTradeOff(data.value.shortest, data.value.safer) : null,
)

const recommendedLabel = computed(() =>
  saferRecommended.value ? 'Safer Alternative' : 'Shortest Route',
)
const recommendationText = computed(() => {
  if (!tradeOff.value) return ''
  if (saferRecommended.value) {
    return `This route has a lower estimated risk based on the factors currently available. It adds about ${tradeOff.value.distanceKm} km and ${tradeOff.value.durationMin} minutes. No route is guaranteed safe.`
  }
  return 'The shortest route has the same or a lower estimated risk, so there is no safety reason to take a detour. No route is guaranteed safe.'
})

// Google Maps me asli route kholne ka link (API key nahi chahiye)
const googleMapsUrl = computed(() => {
  if (!data.value) return '#'
  const params = new URLSearchParams({
    api: '1',
    origin: startName.value || data.value.start,
    destination: data.value.destinationLabel,
    travelmode: 'driving',
  })
  return `https://www.google.com/maps/dir/?${params.toString()}`
})

const errorSuggestions = destinationSuggestions.slice(0, 3)
</script>

<template>
  <div class="container py-4 py-md-5 routes-page">
    <!-- 1. Idle: destination nahi chuna -->
    <section v-if="status === 'idle'" class="sr-card p-4 p-md-5">
      <h1 class="h3 fw-bold mb-3">Safer Route Comparison</h1>
      <StatusMessage type="info" title="No destination selected">
        Analyze a destination first, then choose View Safer Routes to compare routes here.
      </StatusMessage>
      <BaseButton class="mt-4" @click="goHome">Go to Home</BaseButton>
    </section>

    <!-- 2. Loading -->
    <section v-else-if="status === 'loading'" aria-live="polite" aria-busy="true">
      <div class="d-flex align-items-center gap-3 mb-3">
        <div class="spinner-border spinner-border-sm" role="status">
          <span class="visually-hidden">Loading</span>
        </div>
        <span class="fs-5">Loading routes to {{ destinationName }}...</span>
      </div>
      <div class="placeholder-glow">
        <div class="placeholder rounded w-100" style="height: 220px"></div>
      </div>
    </section>

    <!-- 3. Error -->
    <section v-else-if="status === 'error'" class="sr-card p-4 p-md-5">
      <h1 class="h3 fw-bold mb-3">Safer Route Comparison</h1>

      <StatusMessage
        v-if="errorInfo.code === 'NOT_FOUND'"
        type="danger"
        :title="`We could not find &quot;${destinationName}&quot;`"
      >
        The demo covers a small list of Delhi destinations. Try one of these:
        <div class="d-flex flex-wrap gap-2 mt-2">
          <button
            v-for="place in errorSuggestions"
            :key="place"
            type="button"
            class="chip chip-danger"
            @click="tryDestination(place)"
          >
            {{ place }}
          </button>
        </div>
      </StatusMessage>

      <StatusMessage v-else type="danger">
        <div class="d-flex flex-wrap justify-content-between align-items-center gap-2">
          <span>{{ errorInfo.message }}</span>
          <BaseButton @click="loadRoutes">Try again</BaseButton>
        </div>
      </StatusMessage>

      <BaseButton outline class="mt-4" @click="goHome">Go to Home</BaseButton>
    </section>

    <!-- 4. Success -->
    <div v-else-if="status === 'success' && data">
      <header class="routes-heading mb-4">
        <p class="routes-kicker">A BETTER WAY TO GET THERE</p>
        <div class="routes-title-row"><div><h1 class="fw-bold mb-2">The route is part of the journey.</h1><p class="routes-subtitle mb-0">Compare the options, understand the trade-offs, and choose what feels right for you.</p></div><span class="route-counter">ROUTE STUDY <b>01</b></span></div>
        <div class="row g-3 align-items-stretch">
          <div class="col-md-5">
            <div class="endpoint-box p-3 h-100">
              <div class="endpoint-label">START</div>
              <div class="fw-semibold">{{ startName || data.start }}</div>
            </div>
          </div>
          <div class="col-md-5">
            <div class="endpoint-box p-3 h-100">
              <div class="endpoint-label">DESTINATION</div>
              <div class="fw-semibold">{{ data.destinationLabel }}</div>
            </div>
          </div>
          <div class="col-md-2 d-flex align-items-center">
            <span class="text-muted small">Illustrative routes, demo data</span>
          </div>
        </div>
      </header>

      <section aria-label="Route map" class="route-map-section mb-4">
        <div class="map-toolbar"><div><span class="map-toolbar-kicker">THE NEIGHBORHOOD</span><h2>{{ data.destination }}</h2></div><a :href="googleMapsUrl" target="_blank" rel="noopener noreferrer" class="maps-button"><span aria-hidden="true">↗</span> Open directions in Google Maps</a></div>
        <RouteMap :start-name="startName || data.start" :destination-name="data.destination" :show-safer="hasSafer" />
      </section>

      <section aria-labelledby="routes-heading" class="mb-4">
        <h2 id="routes-heading" class="visually-hidden">Route options</h2>
        <div class="row g-3">
          <div class="col-md-6">
            <RouteCard
              label="Shortest Route"
              variant="shortest"
              :distance-km="data.shortest.distanceKm"
              :duration-min="data.shortest.durationMin"
              :score="data.shortest.score"
              :note="data.shortest.note"
              :recommended="shortestRecommended"
            />
          </div>
          <div v-if="hasSafer" class="col-md-6">
            <RouteCard
              label="Safer Alternative"
              variant="safer"
              :distance-km="data.safer.distanceKm"
              :duration-min="data.safer.durationMin"
              :score="data.safer.score"
              :note="data.safer.note"
              :recommended="saferRecommended"
            />
          </div>
          <div v-else class="col-md-6">
            <StatusMessage type="info" title="Route alternatives unavailable" class="h-100">
              Showing one illustrative route. "Safer Alternative" is hidden until data exists.
            </StatusMessage>
          </div>
        </div>
      </section>

      <!-- Trade-off (sirf jab dono routes hon) -->
      <section v-if="tradeOff" class="sr-card p-4 mb-4" aria-labelledby="tradeoff-heading">
        <h2 id="tradeoff-heading" class="endpoint-label mb-3">TRADE-OFF</h2>
        <div class="row g-3 text-center text-md-start mb-3">
          <div class="col-4">
            <div class="tradeoff-value">{{ formatSigned(tradeOff.distanceKm) }} km</div>
            <div class="small text-muted">additional distance</div>
          </div>
          <div class="col-4">
            <div class="tradeoff-value">{{ formatSigned(tradeOff.durationMin) }} min</div>
            <div class="small text-muted">additional time</div>
          </div>
          <div class="col-4">
            <div class="tradeoff-value">{{ formatSigned(tradeOff.scoreDelta) }}</div>
            <div class="small text-muted">safety points</div>
          </div>
        </div>
        <p class="fw-bold mb-1">Recommended: {{ recommendedLabel }}</p>
        <p class="text-muted mb-0">{{ recommendationText }}</p>
      </section>

      <BaseButton outline @click="backToAnalysis">Back to Risk Analysis</BaseButton>
    </div>
  </div>
</template>

<style scoped>
.routes-page{--route-ink:#19382f;--route-muted:#6d7d72;color:var(--route-ink)}
.routes-heading{padding:30px 34px 25px;border-radius:18px;background:radial-gradient(circle at 86% 8%,rgba(196,229,129,.24),transparent 27%),linear-gradient(118deg,#173e35,#28594a);color:#f7f5e9;box-shadow:0 16px 38px rgba(23,62,53,.12)}
.routes-kicker,.map-toolbar-kicker{font-size:.65rem;font-weight:800;letter-spacing:.16em;color:#c5dfaa}.routes-title-row{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-bottom:24px}.routes-title-row h1{font-family:Georgia,'Times New Roman',serif;font-weight:500!important;font-size:clamp(1.9rem,4vw,3rem);letter-spacing:-.045em}.routes-subtitle{max-width:570px;color:rgba(247,245,233,.73);font-size:.91rem}.route-counter{display:flex;align-items:center;gap:9px;color:rgba(241,244,224,.62);font-size:.62rem;letter-spacing:.13em;font-weight:800;white-space:nowrap}.route-counter b{color:#1b4036;background:#c4e581;border-radius:50%;width:30px;height:30px;display:grid;place-items:center;letter-spacing:0}.routes-heading :deep(.endpoint-box){background:rgba(255,255,255,.09);border-color:rgba(242,246,229,.18);border-radius:11px;color:#fff}.routes-heading :deep(.endpoint-label){color:#c5dfaa}.routes-heading .text-muted{color:rgba(247,245,233,.69)!important}
.route-map-section{padding:20px;border-radius:19px;background:#e9eee6;border:1px solid #dbe4d8}.map-toolbar{display:flex;justify-content:space-between;align-items:center;gap:16px;margin:0 0 15px}.map-toolbar-kicker{color:#6b806f}.map-toolbar h2{margin:4px 0 0;font-family:Georgia,'Times New Roman',serif;font-size:1.45rem;font-weight:500;letter-spacing:-.03em}.maps-button{display:inline-flex;align-items:center;gap:9px;background:#c4e581;color:#1a3b30;border-radius:10px;padding:11px 16px;font-size:.77rem;font-weight:800;text-decoration:none;transition:transform .2s,background .2s,box-shadow .2s}.maps-button:hover{background:#b6da70;color:#19392f;transform:translateY(-2px);box-shadow:0 8px 16px rgba(64,105,49,.16)}.maps-button span{font-size:1rem}
.routes-page :deep(.route-card){border:1px solid #e1e8df;border-radius:15px;background:#fff;transition:transform .22s,box-shadow .22s}.routes-page :deep(.route-card:hover){transform:translateY(-3px);box-shadow:0 14px 30px rgba(29,64,47,.09)}.routes-page :deep(.route-card-recommended){border:1.5px solid #78a66e;box-shadow:0 0 0 4px rgba(116,163,103,.1)}.routes-page :deep(.tradeoff-value){font-family:Georgia,serif;color:#315b46}.routes-page :deep(.sr-card){border-radius:15px}.routes-page :deep(.btn){transition:transform .2s,box-shadow .2s}.routes-page :deep(.btn:hover){transform:translateY(-1px);box-shadow:0 6px 14px rgba(22,50,39,.14)}
@media(max-width:767.98px){.routes-heading{padding:24px 19px 20px}.routes-title-row{align-items:flex-start;margin-bottom:18px}.route-counter{display:none}.routes-title-row h1{font-size:2rem}.routes-subtitle{font-size:.84rem}.route-map-section{padding:12px;border-radius:14px}.map-toolbar{align-items:flex-start;flex-direction:column}.maps-button{width:100%;justify-content:center}.routes-page :deep(.row.g-3.text-center){text-align:left!important}}
</style>
