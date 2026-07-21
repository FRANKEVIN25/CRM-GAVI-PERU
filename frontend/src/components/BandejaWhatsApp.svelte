<script>
  let { conversaciones, sedes, clientes, csrf, createUrl } = $props()
  let items = $state([...conversaciones])
  let seleccionadaId = $state(items[0]?.id ?? null)
  let filtro = $state('TODAS')
  let sedeId = $state('')
  let busqueda = $state('')
  let texto = $state('')
  let creando = $state(false)

  let seleccionada = $derived(items.find(item => item.id === seleccionadaId))
  let visibles = $derived(items.filter(item => {
    const coincideSede = !sedeId || item.sede_id === Number(sedeId)
    const coincideFiltro = filtro === 'TODAS' || (filtro === 'NO_LEIDAS' ? item.mensajes.some(m => m.direccion === 'ENTRANTE' && !m.leido) : item.estado === filtro)
    const termino = busqueda.trim().toLowerCase()
    const coincideBusqueda = !termino || `${item.nombre} ${item.telefono}`.toLowerCase().includes(termino)
    return coincideSede && coincideFiltro && coincideBusqueda
  }))

  function hora(iso) { return new Intl.DateTimeFormat('es-PE', { hour: '2-digit', minute: '2-digit' }).format(new Date(iso)) }
  function iniciales(nombre) { return nombre.split(/\s+/).slice(0, 2).map(p => p[0]).join('').toUpperCase() }
  function sinLeer(item) { return item.mensajes.some(m => m.direccion === 'ENTRANTE' && !m.leido) }
  function ultimo(item) { return item.mensajes.at(-1) }

  async function abrir(item) {
    seleccionadaId = item.id
    if (!sinLeer(item)) return
    await fetch(item.abrir_url, { method: 'POST', headers: { 'X-CSRFToken': csrf, 'X-Requested-With': 'XMLHttpRequest' } })
    item.mensajes.forEach(m => { if (m.direccion === 'ENTRANTE') m.leido = true })
    if (item.estado === 'NUEVA') item.estado = 'ABIERTA'
  }

  async function enviar() {
    if (!texto.trim() || !seleccionada) return
    const contenido = texto.trim()
    texto = ''
    const body = new FormData()
    body.append('contenido', contenido)
    body.append('csrfmiddlewaretoken', csrf)
    const res = await fetch(seleccionada.enviar_url, { method: 'POST', body, headers: { 'X-Requested-With': 'XMLHttpRequest' } })
    if (!res.ok) return
    const data = await res.json()
    seleccionada.mensajes.push({ ...data, direccion: 'SALIENTE', leido: true })
    seleccionada.estado = 'ABIERTA'
  }
</script>

<section class="wa-workspace">
  <aside class="wa-workspace__filters">
    <label class="wa-search">⌕ <input bind:value={busqueda} placeholder="Buscar conversaciones" /></label>
    <span class="wa-side-label">Bandejas</span>
    <button class:wa-side-button--active={filtro === 'TODAS'} class="wa-side-button" onclick={() => filtro = 'TODAS'}>Todas las conversaciones <b>{items.length}</b></button>
    <button class:wa-side-button--active={filtro === 'NO_LEIDAS'} class="wa-side-button" onclick={() => filtro = 'NO_LEIDAS'}>No leídas <b>{items.filter(sinLeer).length}</b></button>
    <button class:wa-side-button--active={filtro === 'PENDIENTE'} class="wa-side-button" onclick={() => filtro = 'PENDIENTE'}>Pendientes</button>
    <button class:wa-side-button--active={filtro === 'RESUELTA'} class="wa-side-button" onclick={() => filtro = 'RESUELTA'}>Resueltas</button>
    <span class="wa-side-label">Sedes</span>
    <select bind:value={sedeId} aria-label="Filtrar por sede"><option value="">Todas las sedes</option>{#each sedes as sede}<option value={sede.id}>{sede.nombre}</option>{/each}</select>
  </aside>

  <section class="wa-workspace__list">
    <header><strong>Conversaciones</strong><span>{visibles.length}</span></header>
    {#each visibles as item (item.id)}
      {@const last = ultimo(item)}
      <button class:wa-chat-row--active={item.id === seleccionadaId} class:wa-chat-row--unread={sinLeer(item)} class="wa-chat-row" onclick={() => abrir(item)}>
        <span class="wa-big-avatar">{iniciales(item.nombre)}</span><span class="wa-chat-row__body"><span><strong>{item.nombre}</strong><time>{last ? hora(last.creado) : ''}</time></span><small>{item.sede}</small><em>{last?.contenido || 'Sin mensajes todavía'}</em></span>{#if sinLeer(item)}<i></i>{/if}
      </button>
    {:else}<p class="wa-empty">No hay conversaciones en esta bandeja.</p>{/each}
  </section>

  <main class="wa-workspace__conversation">
    {#if seleccionada}
      <header class="wa-conversation-head"><span class="wa-big-avatar">{iniciales(seleccionada.nombre)}</span><div><strong>{seleccionada.nombre}</strong><small>{seleccionada.telefono} · {seleccionada.sede}</small></div></header>
      <div class="wa-message-area">{#each seleccionada.mensajes as mensaje (mensaje.id)}<div class:wa-bubble--out={mensaje.direccion === 'SALIENTE'} class="wa-bubble">{mensaje.contenido}<small>{hora(mensaje.creado)}</small></div>{/each}</div>
      <form class="wa-composer" onsubmit={(e) => { e.preventDefault(); enviar() }}><input bind:value={texto} placeholder="Escribe un mensaje" /><button type="submit">Enviar</button></form>
    {:else}<div class="wa-empty">Selecciona una conversación para empezar.</div>{/if}
  </main>

  <aside class="wa-workspace__details">
    {#if seleccionada}
      <h2>Datos del contacto</h2><dl><dt>Teléfono</dt><dd>{seleccionada.telefono}</dd><dt>Sede</dt><dd>{seleccionada.sede}</dd><dt>Estado</dt><dd>{seleccionada.estado}</dd></dl>
      <div class="wa-detail-action"><strong>Pipeline comercial</strong><p>{seleccionada.cotizacion ? 'Esta conversación ya tiene una cotización vinculada.' : 'Cuando exista una necesidad concreta, crea una cotización para iniciar el seguimiento.'}</p>
        {#if !seleccionada.cotizacion}
          <button class="btn btn--ghost" type="button" onclick={() => creando = !creando}>+ Crear cotización</button>
          {#if creando}<form method="post" action={createUrl} class="cot-form-rapido"><input type="hidden" name="csrfmiddlewaretoken" value={csrf}/><input type="hidden" name="next" value="bandeja"/><input type="hidden" name="conversacion_id" value={seleccionada.id}/><select required name="cliente"><option value="">Selecciona cliente</option>{#each clientes as cliente}<option value={cliente.id} selected={seleccionada.cliente === cliente.id}>{cliente.nombre} — {cliente.telefono}</option>{/each}</select><textarea required name="descripcion_repuesto" placeholder="Repuesto solicitado"></textarea><input type="hidden" name="descuento_pct" value="0"/><button type="submit" class="btn">Crear oportunidad</button></form>{/if}
        {/if}
      </div>
    {/if}
  </aside>
</section>
