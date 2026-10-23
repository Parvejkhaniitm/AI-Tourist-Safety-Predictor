<script setup>
import { computed } from 'vue'

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
  showSafer: { type: Boolean, default: true },
})

const mapUrl = computed(() => {
  const [lat, lon] = coordinates[props.destinationName] ?? [28.6139, 77.2090]
  const padding = 0.012
  const bbox = [lon - padding, lat - padding, lon + padding, lat + padding].join('%2C')
  return `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik&marker=${lat}%2C${lon}`
})
</script>

<template>
  <figure class="live-map mb-0">
    <iframe
      class="live-map-frame"
      :src="mapUrl"
      :title="`OpenStreetMap showing ${destinationName}`"
      loading="lazy"
      referrerpolicy="no-referrer"
      allowfullscreen
    ></iframe>
    <figcaption class="map-caption">
      <span><span class="map-live-dot"></span> LIVE MAP · {{ destinationName }}</span>
      <span>Map tiles © OpenStreetMap contributors. Route estimates shown below are demo data.</span>
    </figcaption>
  </figure>
</template>

<style scoped>
.live-map{overflow:hidden;border:1px solid #dbe3da;border-radius:18px;background:#e6ebe3;box-shadow:0 14px 34px rgba(22,55,44,.1)}
.live-map-frame{display:block;width:100%;height:390px;border:0;background:#e6ebe3}
.map-caption{display:flex;justify-content:space-between;align-items:center;gap:14px;padding:11px 16px;color:#6b7b70;background:#fff;font-size:.69rem}
.map-caption span:first-child{display:flex;align-items:center;gap:8px;color:#345d48;font-size:.63rem;font-weight:800;letter-spacing:.11em;white-space:nowrap}
.map-live-dot{width:7px;height:7px;border-radius:50%;background:#66a76d;box-shadow:0 0 0 4px #e5f0e3}
@media(max-width:767.98px){.live-map-frame{height:300px}.map-caption{align-items:flex-start;flex-direction:column;gap:5px;font-size:.65rem}}
</style>
