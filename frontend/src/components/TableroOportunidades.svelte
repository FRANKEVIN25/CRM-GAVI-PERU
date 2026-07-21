<script>
  let { oportunidades, etapas, csrf, conversacionesNuevas } = $props()
  let items = $state([...oportunidades])
  let arrastrando = $state(null)
  let error = $state('')
  let busqueda = $state('')

  let termino = $derived(busqueda.trim().toLocaleLowerCase('es-PE'))
  let columnas = $derived(etapas.map(etapa => ({
    ...etapa,
    items: items.filter(item => item.etapa_id === etapa.id && (!termino || `${item.cliente} ${item.titulo} ${item.cotizacion?.descripcion || ''}`.toLocaleLowerCase('es-PE').includes(termino))),
  })))
  let activas = $derived(items.filter(item => !['GANADA', 'PERDIDA'].includes(etapas.find(e => e.id === item.etapa_id)?.tipo)).length)

  function etiquetaDias(dias) { return dias === 0 ? 'Actualizada hoy' : dias === 1 ? 'Actualizada ayer' : `Sin actividad hace ${dias} días` }

  async function mover(etapa) {
    const item = items.find(i => i.id === arrastrando)
    arrastrando = null
    if (!item || item.etapa_id === etapa.id) return
    const anterior = item.etapa_id
    item.etapa_id = etapa.id
    const body = new FormData()
    body.append('etapa_id', etapa.id)
    body.append('csrfmiddlewaretoken', csrf)
    try {
      const res = await fetch(item.update_url, { method: 'POST', body, headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      if (!res.ok) throw new Error(await res.text())
      error = ''
    } catch (e) {
      item.etapa_id = anterior
      error = e.message || 'No se pudo guardar el cambio de etapa.'
    }
  }
</script>

{#if error}<p class="err cot-tablero__error">{error}</p>{/if}
<section class="cot-resumen" aria-label="Resumen comercial">
  <a class="cot-resumen__item" href="/cotizaciones/bandeja/"><span class="cot-resumen__label">Conversaciones por atender</span><strong>{conversacionesNuevas}</strong><span class="cot-resumen__hint">WhatsApp nuevas</span></a>
  <div class="cot-resumen__item"><span class="cot-resumen__label">Oportunidades activas</span><strong>{activas}</strong><span class="cot-resumen__hint">En el pipeline</span></div>
  <div class="cot-resumen__help"><span class="cot-resumen__help-icon">↔</span>Arrastra una oportunidad cuando avance con el cliente.</div>
</section>
<div class="cot-tablero-toolbar"><label class="cot-search"><span>⌕</span><input bind:value={busqueda} type="search" placeholder="Buscar cliente, oportunidad o repuesto" /></label></div>
<div class="cot-tablero" aria-label="Pipeline comercial">
  {#each columnas as columna (columna.id)}
    <section class="cot-columna" aria-label={columna.nombre} ondragover={(e) => e.preventDefault()} ondrop={() => mover(columna)}>
      <div class="cot-columna__header"><div><span class="cot-columna__eyebrow">{columna.tipo === 'EN_PROGRESO' ? 'Pipeline' : 'Cierre'}</span><span class="cot-columna__titulo">{columna.nombre}</span></div><span class="cot-columna__contador">{columna.items.length}</span></div>
      <div class="cot-columna__body">
        {#each columna.items as item (item.id)}
          <article class="cot-tarjeta" draggable="true" ondragstart={() => arrastrando = item.id}>
            <div class="cot-tarjeta__encabezado"><span class="cot-avatar">{item.cliente.split(' ').slice(0,2).map(p => p[0]).join('').toUpperCase()}</span><div class="cot-tarjeta__cliente">{item.cliente}</div></div>
            <p class="cot-tarjeta__producto">{item.titulo || item.cotizacion?.descripcion || 'Oportunidad comercial'}</p>
            {#if item.cotizacion}<span class="cot-codigo">Cotización #{item.cotizacion.id} · {item.cotizacion.estado}</span>{/if}
            <div class="cot-tarjeta__pie"><span class="cot-tarjeta__dias">{etiquetaDias(item.dias_desde_actualizacion)}</span></div>
          </article>
        {:else}<div class="cot-columna__vacio">Sin oportunidades en esta etapa.</div>{/each}
      </div>
    </section>
  {/each}
</div>
