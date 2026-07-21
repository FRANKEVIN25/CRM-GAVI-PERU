import { mount } from 'svelte'
import Timeline from './components/Timeline.svelte'
import InteraccionForm from './components/InteraccionForm.svelte'
import CotizacionesList from './components/CotizacionesList.svelte'
import TableroOportunidades from './components/TableroOportunidades.svelte'
import BandejaWhatsApp from './components/BandejaWhatsApp.svelte'

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
  const oportunidadesEl = document.getElementById('oportunidades-data')
  const etapasEl = document.getElementById('etapas-data')
  mount(TableroOportunidades, {
    target: tableroEl,
    props: {
      oportunidades: oportunidadesEl ? JSON.parse(oportunidadesEl.textContent) : [],
      etapas: etapasEl ? JSON.parse(etapasEl.textContent) : [],
      csrf: tableroEl.dataset.csrf,
      conversacionesNuevas: Number(tableroEl.dataset.conversacionesNuevas || 0),
    },
  })
}

const bandejaEl = document.getElementById('bandeja-root')
if (bandejaEl) {
  const conversacionesEl = document.getElementById('conversaciones-data')
  const sedesEl = document.getElementById('sedes-data')
  const clientesEl = document.getElementById('clientes-data')
  mount(BandejaWhatsApp, { target: bandejaEl, props: {
    conversaciones: conversacionesEl ? JSON.parse(conversacionesEl.textContent) : [],
    sedes: sedesEl ? JSON.parse(sedesEl.textContent) : [],
    clientes: clientesEl ? JSON.parse(clientesEl.textContent) : [],
    csrf: bandejaEl.dataset.csrf, createUrl: bandejaEl.dataset.createUrl,
  } })
}
