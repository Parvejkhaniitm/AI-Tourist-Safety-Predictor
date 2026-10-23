<script setup>
import { onMounted, ref } from 'vue'

defineProps({
  destination: { type: String, default: '' },
})

const shouldPlayVideo = ref(false)
onMounted(() => {
  shouldPlayVideo.value = !window.matchMedia('(prefers-reduced-motion: reduce)').matches && !navigator.connection?.saveData
})
</script>

<template>
  <section class="analysis-loading" aria-live="polite" aria-busy="true">
    <div class="loading-brief">
      <video v-if="shouldPlayVideo" class="loading-brief-video" autoplay muted loop playsinline preload="metadata" aria-hidden="true" tabindex="-1">
        <source src="/cinematic-road.mp4" type="video/mp4" />
      </video>
      <span class="loading-brief-shade" aria-hidden="true"></span>
      <div class="loading-copy">
        <p class="loading-kicker"><span></span> DESTINATION BRIEF</p>
        <h1>Getting to know <em>{{ destination }}</em></h1>
        <p class="loading-description">We’re gathering the available place and travel context for your estimate. This can take a few moments.</p>
        <div class="loading-status"><span class="loading-spinner" aria-hidden="true"></span><span>Preparing your analysis</span></div>
      </div>
      <div class="loading-route-art" aria-hidden="true">
        <span class="loading-sun"></span><span class="loading-orbit"></span>
        <svg viewBox="0 0 440 190" fill="none"><path d="M25 145C105 145 96 56 181 75s66 92 142 52 63-83 96-91"/><circle cx="25" cy="145" r="9"/><circle cx="419" cy="36" r="10"/></svg>
        <span class="loading-art-label">A MOMENT, PLEASE</span>
      </div>
    </div>
    <div class="loading-preview" aria-hidden="true">
      <div class="preview-score"><span class="skeleton-line short"></span><span class="score-ring"></span><span class="skeleton-line"></span></div>
      <div class="preview-reasons"><span class="skeleton-line medium"></span><span v-for="n in 3" :key="n" class="reason-skeleton"><i></i><span class="skeleton-line"></span></span></div>
    </div>
    <aside class="loading-journey-note" aria-label="What the analysis checks">
      <video v-if="shouldPlayVideo" class="journey-note-video" autoplay muted loop playsinline preload="metadata" aria-hidden="true" tabindex="-1">
        <source src="/cinematic-mountain-view.mp4" type="video/mp4" />
      </video>
      <span class="journey-note-shade" aria-hidden="true"></span>
      <div class="journey-note-copy">
        <span class="journey-note-kicker"><i></i> WHILE WE PUT YOUR BRIEF TOGETHER</span>
        <h2>Useful context<br />for the road ahead.</h2>
        <p>We’re bringing the available signals into one clear destination view.</p>
      </div>
      <ul class="journey-checklist">
        <li><span class="journey-check-icon">⌖</span><span><strong>Place context</strong><small>Location and nearby map details</small></span></li>
        <li><span class="journey-check-icon">◷</span><span><strong>Visit conditions</strong><small>Selected time and available weather</small></span></li>
        <li><span class="journey-check-icon">↗</span><span><strong>Risk estimate</strong><small>Score and the signals behind it</small></span></li>
      </ul>
      <span class="journey-note-index" aria-hidden="true">TRAVEL NOTES / 04</span>
    </aside>
  </section>
</template>

<style scoped>
.analysis-loading{display:grid;gap:16px;color:#17392f}
.loading-brief{position:relative;isolation:isolate;min-height:245px;display:grid;grid-template-columns:1.1fr .9fr;align-items:center;overflow:hidden;padding:32px 36px;border-radius:18px;background:radial-gradient(ellipse at 76% 10%,rgba(196,229,129,.22),transparent 31%),linear-gradient(116deg,#132f2b,#28584b);color:#f7f5ea;box-shadow:0 18px 42px rgba(21,54,46,.1)}
.loading-brief-video,.loading-brief-shade{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}.loading-brief-video{z-index:-2;object-fit:cover;object-position:center 57%;opacity:.48;filter:saturate(.72)}.loading-brief-shade{z-index:-1;background:linear-gradient(90deg,rgba(8,24,25,.9) 0%,rgba(10,31,29,.76) 45%,rgba(13,41,35,.43) 100%),linear-gradient(0deg,rgba(8,21,22,.28),transparent 56%)}
.loading-copy{position:relative;z-index:1;max-width:490px}.loading-kicker{display:flex;align-items:center;gap:9px;margin:0 0 15px;color:#c4d9b6;font-size:.63rem;letter-spacing:.15em;font-weight:800}.loading-kicker span{width:7px;height:7px;border-radius:50%;background:#c4e581;box-shadow:0 0 0 4px rgba(196,229,129,.15)}
.loading-copy h1{font-family:Georgia,'Times New Roman',serif;font-size:clamp(2rem,4vw,3.3rem);font-weight:500;letter-spacing:-.045em;line-height:1.03;margin:0 0 12px}.loading-copy h1 em{color:#c4e581;font-weight:400}.loading-description{max-width:410px;color:rgba(247,245,234,.73);font-size:.88rem;line-height:1.65;margin:0 0 19px}.loading-status{display:inline-flex;align-items:center;gap:9px;padding:8px 12px;border:1px solid rgba(248,247,234,.18);border-radius:999px;background:rgba(255,255,255,.07);font-size:.72rem;color:#f1f2e4}.loading-spinner{width:13px;height:13px;border:2px solid rgba(244,245,226,.35);border-top-color:#c4e581;border-radius:50%;animation:loading-spin .8s linear infinite}
.loading-route-art{position:relative;min-height:185px;display:grid;place-items:center}.loading-sun{position:absolute;right:20%;top:2%;width:62px;height:62px;border-radius:50%;background:linear-gradient(140deg,#dfe6ae,#ddb991);box-shadow:0 0 45px rgba(222,211,159,.18)}.loading-orbit{position:absolute;width:87%;height:72%;border:1px solid rgba(236,243,216,.14);border-radius:50%;transform:rotate(-16deg)}.loading-route-art svg{position:relative;width:100%;z-index:1;overflow:visible}.loading-route-art svg path{stroke:#e7e9c8;stroke-width:3;stroke-linecap:round;stroke-dasharray:7 9;animation:loading-dash 1.2s linear infinite}.loading-route-art svg circle:first-of-type{fill:#c4e581;stroke:#f1f3dc;stroke-width:4}.loading-route-art svg circle:last-of-type{fill:#e9dfb4;stroke:#f9f5e6;stroke-width:4}.loading-art-label{position:absolute;right:5%;bottom:0;color:rgba(237,242,222,.58);font-size:.55rem;font-weight:800;letter-spacing:.14em}
.loading-preview{display:grid;grid-template-columns:.82fr 1.18fr;gap:14px}.preview-score,.preview-reasons{min-height:176px;padding:20px;border:1px solid #dce5d9;border-radius:15px;background:linear-gradient(145deg,#fff,#f4f6ef)}.preview-score{display:flex;flex-direction:column;align-items:center;justify-content:space-between;gap:14px}.preview-reasons{display:flex;flex-direction:column;gap:17px}.skeleton-line{display:block;width:72%;height:10px;border-radius:99px;background:linear-gradient(90deg,#e9eee5 25%,#f7f8f4 45%,#e9eee5 65%);background-size:240% 100%;animation:loading-shimmer 1.6s ease-in-out infinite}.skeleton-line.short{width:28%}.skeleton-line.medium{width:46%;height:13px}.preview-score>.skeleton-line:last-child{width:65%}.score-ring{display:block;width:94px;height:94px;border:10px solid #e9eee6;border-top-color:#b8d28c;border-radius:50%;animation:loading-spin 2.4s linear infinite}.reason-skeleton{display:flex;align-items:center;gap:12px}.reason-skeleton i{width:26px;height:26px;flex:0 0 26px;border-radius:9px;background:#e7eee2}.reason-skeleton .skeleton-line{width:84%}
.loading-journey-note{position:relative;isolation:isolate;min-height:226px;display:grid;grid-template-columns:1fr .9fr;align-items:center;gap:24px;overflow:hidden;padding:25px 30px;border:1px solid #30494a;border-radius:16px;background:#102125;color:#edf2e9;box-shadow:0 18px 45px rgba(0,0,0,.14)}.journey-note-video,.journey-note-shade{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}.journey-note-video{z-index:-2;object-fit:cover;object-position:center 54%;opacity:.55;filter:saturate(.75)}.journey-note-shade{z-index:-1;background:linear-gradient(90deg,rgba(6,20,23,.9),rgba(8,25,27,.7) 49%,rgba(8,25,27,.46)),linear-gradient(0deg,rgba(6,18,21,.55),transparent)}.journey-note-copy,.journey-checklist{position:relative;z-index:1}.journey-note-kicker{display:flex;align-items:center;gap:9px;color:#c9e99d;font-size:.58rem;font-weight:800;letter-spacing:.14em}.journey-note-kicker i{width:7px;height:7px;border-radius:50%;background:#c7f36b;box-shadow:0 0 0 4px rgba(199,243,107,.14)}.journey-note-copy h2{margin:10px 0 8px;color:#f2f0e5;font:500 clamp(1.55rem,3vw,2.2rem)/1.02 Georgia,'Times New Roman',serif;letter-spacing:-.04em}.journey-note-copy p{max-width:360px;margin:0;color:#bac8bf;font-size:.76rem;line-height:1.55}.journey-checklist{display:grid;gap:8px;margin:0;padding:0;list-style:none}.journey-checklist li{display:flex;align-items:center;gap:11px;padding:9px 12px;border:1px solid rgba(204,226,196,.19);border-radius:11px;background:rgba(11,28,30,.5);backdrop-filter:blur(5px)}.journey-check-icon{display:grid;place-items:center;flex:0 0 29px;width:29px;height:29px;border-radius:9px;background:#c7f36b;color:#182820;font-size:.9rem;font-weight:800}.journey-checklist strong,.journey-checklist small{display:block}.journey-checklist strong{color:#f0f3e9;font-size:.72rem}.journey-checklist small{margin-top:2px;color:#aebdb5;font-size:.62rem}.journey-note-index{position:absolute;right:17px;bottom:13px;color:rgba(232,241,226,.63);font-size:.49rem;font-weight:800;letter-spacing:.13em}
@keyframes loading-spin{to{transform:rotate(360deg)}}@keyframes loading-dash{to{stroke-dashoffset:-32}}@keyframes loading-shimmer{to{background-position:-240% 0}}
@media(max-width:767.98px){.loading-brief{grid-template-columns:1fr;padding:26px 21px 19px;border-radius:15px}.loading-route-art{min-height:140px;margin:0 -10px}.loading-route-art svg{max-width:430px}.loading-preview{grid-template-columns:1fr}.preview-score{min-height:150px}.preview-reasons{min-height:150px}.loading-journey-note{grid-template-columns:1fr;gap:16px;min-height:0;padding:21px 18px 29px}.journey-note-copy h2{font-size:1.8rem}.journey-checklist li{padding:8px 10px}.journey-note-index{font-size:.44rem}}
@media(prefers-reduced-motion:reduce){.loading-spinner,.loading-route-art svg path,.score-ring,.skeleton-line{animation:none}.loading-route-art svg path{stroke-dasharray:none}}
</style>
