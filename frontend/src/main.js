import { mount } from 'svelte'
import Timeline from './components/Timeline.svelte'
import InteraccionForm from './components/InteraccionForm.svelte'
import CotizacionesList from './components/CotizacionesList.svelte'
import TableroVendedor from './components/TableroVendedor.svelte'

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

// ── Cotizaciones ──────────────────────────────────────────────────────────
const cotizacionesEl = document.getElementById('cotizaciones-root')
if (cotizacionesEl) {
  const dataEl = document.getElementById('cotizaciones-data')
  const cotizaciones = dataEl ? JSON.parse(dataEl.textContent) : []
  mount(CotizacionesList, {
    target: cotizacionesEl,
    props: { cotizaciones, csrf: cotizacionesEl.dataset.csrf },
  })
}

// ── Tablero Kanban del vendedor (incluye WhatsApp: mensajes nuevos + chat) ─
const tableroEl = document.getElementById('tablero-root')
if (tableroEl) {
  const dataEl = document.getElementById('tablero-data')
  const estadosEl = document.getElementById('estados-data')
  const clientesEl = document.getElementById('clientes-data')
  mount(TableroVendedor, {
    target: tableroEl,
    props: {
      cotizaciones: dataEl ? JSON.parse(dataEl.textContent) : [],
      estados: estadosEl ? JSON.parse(estadosEl.textContent) : [],
      clientes: clientesEl ? JSON.parse(clientesEl.textContent) : [],
      csrf: tableroEl.dataset.csrf,
      createUrl: tableroEl.dataset.createUrl,
    },
  })
}
