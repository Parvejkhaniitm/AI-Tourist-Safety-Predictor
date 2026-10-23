<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const coordinates = {
  'India Gate': [28.6129, 77.2295],
  'Red Fort': [28.6562, 77.2410],
  'Qutub Minar': [28.5245, 77.1855],
  "Humayun's Tomb": [28.5933, 77.2507],
  'Lotus Temple': [28.5535, 77.2588],
}

const props = defineProps({
  startName: { type: String, default: 'Start' },
  destinationName: { type: String, required: true },
  showAlternative: { type: Boolean, default: true },
  alternativeIsSafer: { type: Boolean, default: false },
  shortestPath: { type: Array, default: () => [] },
  saferPath: { type: Array, default: () => [] },
})

const mapElement = ref(null)
let map
let routeLayers = []

function validPath(path) {
  return Array.isArray(path) ? path.filter((point) => Number.isFinite(point?.lat) && Number.isFinite(point?.lng)) : []
}

function drawRoutes() {
  if (!map) return
  routeLayers.forEach((layer) => layer.remove())
  routeLayers = []

  const shortest = validPath(props.shortestPath)
  const safer = validPath(props.saferPath)
  const points = []

  for (const [path, color, weight, opacity] of [
    [shortest, '#173e35', 6, 0.92],
    [safer, props.alternativeIsSafer ? '#78a66e' : '#d48a38', 5, 0.92],
  ]) {
    if (path.length < 2) continue
    const line = L.polyline(path.map(({ lat, lng }) => [lat, lng]), { color, weight, opacity, lineCap: 'round', lineJoin: 'round' }).addTo(map)
    routeLayers.push(line)
    points.push(...path.map(({ lat, lng }) => [lat, lng]))
  }

  const primary = shortest.length ? shortest : safer
  if (primary.length) {
    const first = primary[0]
    const last = primary[primary.length - 1]
    routeLayers.push(L.circleMarker([first.lat, first.lng], { radius: 8, color: '#fff', weight: 3, fillColor: '#173e35', fillOpacity: 1 }).bindPopup(`Start · ${props.startName}`).addTo(map))
    routeLayers.push(L.circleMarker([last.lat, last.lng], { radius: 9, color: '#fff', weight: 3, fillColor: '#d46f4b', fillOpacity: 1 }).bindPopup(props.destinationName).addTo(map))
    if (points.length) map.fitBounds(L.latLngBounds(points), { padding: [30, 30], maxZoom: 15 })
  } else {
    const [lat, lng] = coordinates[props.destinationName] ?? [28.6139, 77.2090]
    map.setView([lat, lng], 14)
  }
}

onMounted(() => {
  map = L.map(mapElement.value, { scrollWheelZoom: false, zoomControl: true })
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map)
  drawRoutes()
})

watch(() => [props.shortestPath, props.saferPath, props.destinationName, props.alternativeIsSafer], drawRoutes, { deep: true })
onBeforeUnmount(() => { map?.remove(); map = null })
</script>

<template>
  <figure class="live-map mb-0">
    <div ref="mapElement" class="live-map-frame" role="region" :aria-label="`OpenStreetMap route from ${startName} to ${destinationName}`"></div>
    <figcaption class="map-caption">
      <span><span class="map-live-dot"></span> LIVE MAP · {{ destinationName }}</span>
      <span class="map-legend">
        <span><i class="map-line map-line-shortest"></i> Shortest route</span>
        <span v-if="showAlternative"><i class="map-line" :class="alternativeIsSafer ? 'map-line-safer' : 'map-line-alternative'"></i> {{ alternativeIsSafer ? 'Lower-risk alternative' : 'Alternative route' }}</span>
      </span>
      <span>Map tiles © OpenStreetMap contributors. Compare live road options below.</span>
    </figcaption>
  </figure>
</template>

<style scoped>
.live-map{overflow:hidden;border:1px solid #dbe3da;border-radius:18px;background:#e6ebe3;box-shadow:0 14px 34px rgba(22,55,44,.1)}
.live-map-frame{display:block;width:100%;height:390px;background:#e6ebe3}
.map-caption{display:flex;justify-content:space-between;align-items:center;gap:14px;padding:11px 16px;color:#6b7b70;background:#fff;font-size:.69rem}
.map-caption>span:first-child{display:flex;align-items:center;gap:8px;color:#345d48;font-size:.63rem;font-weight:800;letter-spacing:.11em;white-space:nowrap}
.map-live-dot{width:7px;height:7px;border-radius:50%;background:#66a76d;box-shadow:0 0 0 4px #e5f0e3}
.map-legend{display:flex;align-items:center;gap:13px;color:#50635a;font-size:.67rem;white-space:nowrap}.map-legend>span{display:flex;align-items:center;gap:6px}.map-line{width:17px;height:4px;border-radius:6px}.map-line-shortest{background:#173e35}.map-line-safer{background:#78a66e}.map-line-alternative{background:#d48a38}
@media(max-width:767.98px){.live-map-frame{height:300px}.map-caption{align-items:flex-start;flex-direction:column;gap:8px;font-size:.65rem}.map-legend{white-space:normal;flex-wrap:wrap}}
</style>
