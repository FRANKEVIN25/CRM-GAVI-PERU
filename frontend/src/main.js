import { mount } from 'svelte'
import Timeline from './components/Timeline.svelte'
import InteraccionForm from './components/InteraccionForm.svelte'

// ── Timeline ────────────────────────────────────────────────────────────────
const timelineEl = document.getElementById('timeline-root')
if (timelineEl) {
  const dataEl = document.getElementById('interacciones-data')
  const interacciones = dataEl ? JSON.parse(dataEl.textContent) : []
  mount(Timeline, { target: timelineEl, props: { interacciones } })
}

// ── Formulario de interacción ────────────────────────────────────────────────
const formEl = document.getElementById('interaccion-form-root')
if (formEl) {
  mount(InteraccionForm, {
    target: formEl,
    props: {
      addUrl:   formEl.dataset.addUrl,
      csrf:     formEl.dataset.csrf,
      username: formEl.dataset.username,
    },
  })
}
