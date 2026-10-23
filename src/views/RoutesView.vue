<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import BaseButton from '../components/BaseButton.vue'
import StatusMessage from '../components/StatusMessage.vue'
import RouteCard from '../components/RouteCard.vue'
import RouteMap from '../components/RouteMap.vue'
import { fetchRoutes, getCachedRoutes } from '../services/api'
import { getTradeOff, getRecommendedRoute, formatSigned } from '../utils/routes'

const route = useRoute()
const router = useRouter()

// --- State: idle | loading | success | error ---
const status = ref('idle')
const data = ref(null)
const errorInfo = ref(null)
const shouldPlayVideo = ref(false)

onMounted(() => {
  shouldPlayVideo.value = !window.matchMedia('(prefers-reduced-motion: reduce)').matches && !navigator.connection?.saveData
})

const destinationName = computed(() => String(route.query.destination ?? '').trim())
const startName = computed(() => String(route.query.start ?? '').trim())
const startCoordinates = computed(() => {
  const lat = Number(route.query.startLat)
  const lng = Number(route.query.startLng)
  return Number.isFinite(lat) && Number.isFinite(lng) ? { lat, lng } : null
})


async function loadRoutes() {
  if (!destinationName.value) {
    status.value = 'idle'
    data.value = null
    return
  }

  const requested = destinationName.value
  const cached = getCachedRoutes(requested, startName.value, startCoordinates.value)
  if (cached) {
    data.value = cached
    status.value = 'success'
    errorInfo.value = null
    return
  }
  status.value = 'loading'
  errorInfo.value = null

  try {
    const result = await fetchRoutes(requested, startName.value, startCoordinates.value)
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
    query: {
      destination: data.value.destination,
      ...(startName.value && { start: startName.value }),
      ...(startCoordinates.value && { startLat: startCoordinates.value.lat, startLng: startCoordinates.value.lng }),
    },
  })
}
// --- Derived values (saara hisaab utils/routes.js me hai) ---
const hasAlternative = computed(() => !!data.value?.alternative)
const hasSafer = computed(() => hasAlternative.value && data.value.alternative.score !== null && data.value.alternative.score < data.value.shortest.score)

const recommendedKey = computed(() =>
  data.value ? getRecommendedRoute(data.value.shortest, data.value.alternative) : null,
)
const saferRecommended = computed(() => hasSafer.value && recommendedKey.value === 'safer')
const shortestRecommended = computed(() => hasAlternative.value && recommendedKey.value === 'shortest')

const tradeOff = computed(() =>
  hasAlternative.value ? getTradeOff(data.value.shortest, data.value.alternative) : null,
)

const recommendedLabel = computed(() =>
  saferRecommended.value ? 'Safer Alternative' : 'Shortest Route',
)
const recommendationText = computed(() => {
  if (!tradeOff.value) return ''
  if (saferRecommended.value) {
    return `It scores ${data.value.alternative.score}/100 versus ${data.value.shortest.score}/100 for the shortest option, using the available route samples. It adds about ${tradeOff.value.distanceKm} km and ${tradeOff.value.durationMin} minutes. No route is guaranteed safe.`
  }
  return `The alternative scores ${data.value.alternative.score ?? 'unavailable'}/100 versus ${data.value.shortest.score ?? 'unavailable'} for the shortest route. The shortest route is recommended because the available data does not show a lower risk on the alternative. No route is guaranteed safe.`
})

// Google Maps me asli route kholne ka link (API key nahi chahiye)
const googleMapsUrl = computed(() => {
  if (!data.value) return '#'
  const params = new URLSearchParams({
    api: '1',
    origin: startCoordinates.value ? `${startCoordinates.value.lat},${startCoordinates.value.lng}` : (startName.value || data.value.start),
    destination: data.value.destinationLabel,
    travelmode: 'driving',
  })
  return `https://www.google.com/maps/dir/?${params.toString()}`
})

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
    <section v-else-if="status === 'loading'" class="route-loading" aria-live="polite" aria-busy="true">
      <div class="route-loading-copy">
        <div>
          <p class="routes-kicker mb-2">ROUTE STUDY · IN PROGRESS</p>
          <h1>Tracing the roads between your places.</h1>
          <p>{{ startName || 'Your starting point' }} <span aria-hidden="true">→</span> {{ destinationName }}</p>
        </div>
        <span class="route-loading-mark" aria-hidden="true"><i></i><i></i><i></i></span>
      </div>
      <div class="route-loading-map" aria-hidden="true">
        <video v-if="shouldPlayVideo" class="route-loading-video" autoplay muted loop playsinline preload="metadata" tabindex="-1">
          <source src="/cinematic-route-mountain.mp4" type="video/mp4" />
        </video>
        <span class="route-loading-shade"></span>
        <span class="route-loading-road road-one"></span><span class="route-loading-road road-two"></span>
        <svg viewBox="0 0 800 210" preserveAspectRatio="none"><path d="M36 165C146 150 145 58 280 91s136 88 249 40 123-72 235-83" /></svg>
        <span class="route-loading-pin pin-origin"></span><span class="route-loading-pin pin-destination"></span>
        <span class="route-map-caption">CONNECTING TO THE ROAD NETWORK</span>
      </div>
      <div class="route-loading-cards" aria-hidden="true"><span></span><span></span></div>
    </section>

    <!-- 3. Error -->
    <section v-else-if="status === 'error'" class="sr-card p-4 p-md-5">
      <h1 class="h3 fw-bold mb-3">Safer Route Comparison</h1>

      <StatusMessage type="danger" :title="errorInfo.code === 'NOT_FOUND' ? 'Could not locate a route endpoint' : 'Route lookup failed'">
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
            <span class="text-muted small">Roads via {{ data.provider || 'demo data' }} · risk is estimated</span>
          </div>
        </div>
      </header>

      <section aria-label="Route map" class="route-map-section mb-4">
        <div class="map-toolbar"><div><span class="map-toolbar-kicker">THE NEIGHBORHOOD</span><h2>{{ data.destination }}</h2></div><a :href="googleMapsUrl" target="_blank" rel="noopener noreferrer" class="maps-button"><span aria-hidden="true">↗</span> Open directions in Google Maps</a></div>
        <RouteMap
          :start-name="startName || data.start"
          :destination-name="data.destination"
          :show-alternative="hasAlternative"
          :alternative-is-safer="hasSafer"
          :shortest-path="data.shortest.path || []"
          :safer-path="data.alternative?.path || []"
        />
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
          <div v-if="hasAlternative" class="col-md-6">
            <RouteCard
              :label="hasSafer ? 'Safer Alternative' : 'Alternative Route'"
              variant="safer"
              :distance-km="data.alternative.distanceKm"
              :duration-min="data.alternative.durationMin"
              :score="data.alternative.score"
              :note="data.alternative.note"
              :recommended="saferRecommended"
            />
          </div>
          <div v-else class="col-md-6">
            <StatusMessage type="info" title="No alternate route returned" class="h-100">
              The routing provider returned only one road option for these locations. This is a routing-data limitation, not a restriction on your entered start point. {{ data.shortest.riskExplanation }} You can still open directions in Google Maps.
            </StatusMessage>
          </div>
        </div>
      </section>

      <!-- Trade-off (sirf jab dono routes hon) -->
      <section v-if="tradeOff" class="sr-card p-4 mb-4" aria-labelledby="tradeoff-heading">
        <h2 id="tradeoff-heading" class="endpoint-label mb-3">ROUTE COMPARISON</h2>
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
            <div class="small text-muted">estimated risk points</div>
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
.route-loading{display:grid;gap:15px}.route-loading-copy{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:26px 32px;border-radius:17px;background:linear-gradient(116deg,#173e35,#28594a);color:#f7f5e9;box-shadow:0 16px 36px rgba(23,62,53,.1)}.route-loading-copy .routes-kicker{color:#c5dfaa}.route-loading-copy h1{max-width:610px;margin:0 0 9px;font-family:Georgia,'Times New Roman',serif;font-size:clamp(1.8rem,4vw,2.8rem);font-weight:500;letter-spacing:-.04em}.route-loading-copy p:last-child{margin:0;color:rgba(247,245,233,.73);font-size:.9rem}.route-loading-copy p:last-child span{padding:0 8px;color:#c4e581}.route-loading-mark{position:relative;display:block;width:74px;height:74px;flex:0 0 74px;border:1px solid rgba(241,246,225,.22);border-radius:50%}.route-loading-mark:before,.route-loading-mark:after{position:absolute;content:'';inset:9px;border:1px solid rgba(241,246,225,.18);border-radius:50%}.route-loading-mark:after{inset:19px}.route-loading-mark i{position:absolute;z-index:1;width:8px;height:8px;border-radius:50%;background:#c4e581;top:50%;left:50%;transform:translate(-50%,-50%);animation:route-pulse 1.3s ease-in-out infinite alternate}.route-loading-mark i:nth-child(2){margin-left:-23px;animation-delay:.18s}.route-loading-mark i:nth-child(3){margin-left:23px;animation-delay:.36s}.route-loading-map{position:relative;isolation:isolate;height:275px;overflow:hidden;border:1px solid #345052!important;border-radius:17px;background:#102326!important;background-image:none!important;filter:none!important}.route-loading-video,.route-loading-shade{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}.route-loading-video{z-index:0;object-fit:cover;object-position:center 52%;opacity:.79;filter:brightness(.73) saturate(.82)}.route-loading-shade{z-index:1;background:linear-gradient(90deg,rgba(8,21,22,.38),rgba(9,24,25,.12) 50%,rgba(8,20,22,.38)),linear-gradient(0deg,rgba(6,17,20,.54),rgba(6,17,20,.08) 56%)}.route-loading-road{position:absolute;z-index:2;height:1px;width:120%;left:-10%;background:rgba(234,244,226,.24);transform:rotate(-13deg);top:35%}.road-two{transform:rotate(12deg);top:72%}.route-loading-map svg{position:absolute;z-index:3;inset:0;width:100%;height:100%}.route-loading-map svg path{fill:none;stroke:#c7f36b;stroke-width:7;stroke-linecap:round;stroke-dasharray:11 14;filter:drop-shadow(0 2px 6px rgba(0,0,0,.7));animation:route-path 1.4s linear infinite}.route-loading-pin{position:absolute;z-index:4;top:69%;left:5%;width:17px;height:17px;border:4px solid #fff;border-radius:50%;background:#173e35;box-shadow:0 2px 10px rgba(0,0,0,.65)}.pin-destination{top:20%;left:auto;right:5%;background:#d46f4b}.route-map-caption{position:absolute;z-index:5;right:17px;bottom:15px;padding:8px 11px;border:1px solid rgba(255,255,255,.22);border-radius:999px;background:rgba(10,25,27,.72);color:#eff3e9;font-size:.57rem;font-weight:800;letter-spacing:.12em;backdrop-filter:blur(8px)}.route-loading-cards{display:grid;grid-template-columns:1fr 1fr;gap:14px}.route-loading-cards span{height:112px;border:1px solid #dce5d9;border-radius:15px;background:linear-gradient(100deg,#fff 25%,#edf1e9 42%,#fff 60%);background-size:240% 100%;animation:route-shimmer 1.6s ease-in-out infinite}@keyframes route-pulse{to{opacity:.42;transform:translate(-50%,-50%) scale(.72)}}@keyframes route-path{to{stroke-dashoffset:-50}}@keyframes route-shimmer{to{background-position:-240% 0}}
.routes-heading{position:relative;isolation:isolate;overflow:hidden;padding:30px 34px 25px;border-radius:18px;background:#173e35;color:#f7f5e9;box-shadow:0 16px 38px rgba(23,62,53,.12)}
.routes-kicker,.map-toolbar-kicker{font-size:.65rem;font-weight:800;letter-spacing:.16em;color:#c5dfaa}.routes-title-row{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-bottom:24px}.routes-title-row h1{font-family:Georgia,'Times New Roman',serif;font-weight:500!important;font-size:clamp(1.9rem,4vw,3rem);letter-spacing:-.045em}.routes-subtitle{max-width:570px;color:rgba(247,245,233,.73);font-size:.91rem}.route-counter{display:flex;align-items:center;gap:9px;color:rgba(241,244,224,.62);font-size:.62rem;letter-spacing:.13em;font-weight:800;white-space:nowrap}.route-counter b{color:#1b4036;background:#c4e581;border-radius:50%;width:30px;height:30px;display:grid;place-items:center;letter-spacing:0}.routes-heading :deep(.endpoint-box){background:rgba(255,255,255,.09);border-color:rgba(242,246,229,.18);border-radius:11px;color:#fff}.routes-heading :deep(.endpoint-label){color:#c5dfaa}.routes-heading .text-muted{color:rgba(247,245,233,.69)!important}
.route-map-section{padding:20px;border-radius:19px;background:#e9eee6;border:1px solid #dbe4d8}.map-toolbar{display:flex;justify-content:space-between;align-items:center;gap:16px;margin:0 0 15px}.map-toolbar-kicker{color:#6b806f}.map-toolbar h2{margin:4px 0 0;font-family:Georgia,'Times New Roman',serif;font-size:1.45rem;font-weight:500;letter-spacing:-.03em}.maps-button{display:inline-flex;align-items:center;gap:9px;background:#c4e581;color:#1a3b30;border-radius:10px;padding:11px 16px;font-size:.77rem;font-weight:800;text-decoration:none;transition:transform .2s,background .2s,box-shadow .2s}.maps-button:hover{background:#b6da70;color:#19392f;transform:translateY(-2px);box-shadow:0 8px 16px rgba(64,105,49,.16)}.maps-button span{font-size:1rem}
.routes-page :deep(.route-card){border:1px solid #e1e8df;border-radius:15px;background:#fff;transition:transform .22s,box-shadow .22s}.routes-page :deep(.route-card:hover){transform:translateY(-3px);box-shadow:0 14px 30px rgba(29,64,47,.09)}.routes-page :deep(.route-card-recommended){border:1.5px solid #78a66e;box-shadow:0 0 0 4px rgba(116,163,103,.1)}.routes-page :deep(.tradeoff-value){font-family:Georgia,serif;color:#315b46}.routes-page :deep(.sr-card){border-radius:15px}.routes-page :deep(.btn){transition:transform .2s,box-shadow .2s}.routes-page :deep(.btn:hover){transform:translateY(-1px);box-shadow:0 6px 14px rgba(22,50,39,.14)}
@media(max-width:767.98px){.routes-heading{padding:24px 19px 20px}.routes-title-row{align-items:flex-start;margin-bottom:18px}.route-counter{display:none}.routes-title-row h1{font-size:2rem}.routes-subtitle{font-size:.84rem}.route-map-section{padding:12px;border-radius:14px}.map-toolbar{align-items:flex-start;flex-direction:column}.maps-button{width:100%;justify-content:center}.routes-page :deep(.row.g-3.text-center){text-align:left!important}}
@media(max-width:767.98px){.route-loading-copy{padding:23px 20px;border-radius:15px}.route-loading-mark{width:54px;height:54px;flex-basis:54px}.route-loading-mark i:nth-child(2){margin-left:-16px}.route-loading-mark i:nth-child(3){margin-left:16px}.route-loading-map{height:220px;border-radius:14px}.route-loading-cards{grid-template-columns:1fr}.route-loading-cards span{height:90px}.route-map-caption{right:9px;bottom:9px;font-size:.5rem}}
@media(prefers-reduced-motion:reduce){.route-loading-mark i,.route-loading-map svg path,.route-loading-cards span{animation:none}.route-loading-map svg path{stroke-dasharray:none}}
</style>
