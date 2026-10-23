import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'
// Hamari theme Bootstrap ke BAAD import hoti hai, taaki hamare overrides jeetein
import './assets/theme.css'

const app = createApp(App)
app.use(router)
app.mount('#app')