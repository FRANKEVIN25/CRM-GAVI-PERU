<script>
  import ChatFlotante from './ChatFlotante.svelte'
  import { crearControladorChats, iniciales, normalizarTelefono } from '../lib/chats.svelte.js'

  // El tablero recibe solo las cotizaciones del vendedor desde Django. La
  // bandeja es compartida: un mensaje nuevo aun no pertenece a nadie hasta
  // que se cree una cotizacion desde esa conversacion.
  let { cotizaciones, estados, clientes, csrf, createUrl } = $props()

  let items = $state([...cotizaciones])
  let error = $state('')
  let busqueda = $state('')
  let soloPendientes = $state(false)
  let arrastrandoId = $state(null)
  let creandoDesde = $state(null)

  const chats = crearControladorChats()

  let termino = $derived(busqueda.trim().toLocaleLowerCase('es-PE'))
  let telefonosConCotizacion = $derived(
    new Set(items.map(i => normalizarTelefono(i.cliente_telefono)))
  )
  let mensajesNuevos = $derived(
    chats.conversaciones.filter(c => {
      const coincide = !termino || [c.nombre, c.telefono, c.ultimoMensaje]
        .filter(Boolean).some(valor => valor.toLocaleLowerCase('es-PE').includes(termino))
      return !telefonosConCotizacion.has(normalizarTelefono(c.telefono)) && coincide
    })
  )
  let columnas = $derived(
    estados.map(([value, label]) => ({
      value,
      label,
      items: items.filter(i => {
        const coincide = !termino || [i.cliente, i.descripcion_repuesto, i.codigo_producto]
          .filter(Boolean).some(valor => valor.toLocaleLowerCase('es-PE').includes(termino))
        const pendiente = !soloPendientes || !['CONVERTIDA', 'PERDIDA'].includes(i.estado)
        return i.estado === value && coincide && pendiente
      }),
    }))
  )
  let totalActivas = $derived(items.filter(i => !['CONVERTIDA', 'PERDIDA'].includes(i.estado)).length)

  function clienteSugerido(conv) {
    const buscado = normalizarTelefono(conv.telefono)
    return clientes.find(c => normalizarTelefono(c.telefono) === buscado)
  }

  function etiquetaDias(dias) {
    if (dias === 0) return 'Actualizada hoy'
    if (dias === 1) return 'Actualizada ayer'
    return `Sin actividad hace ${dias} días`
  }

  function handleDragStart(item) {
    arrastrandoId = item.id
  }

  function handleDrop(nuevoEstado) {
    const id = arrastrandoId
    arrastrandoId = null
    if (id == null) return

    const item = items.find(i => i.id === id)
    if (!item || item.estado === nuevoEstado) return

    const anterior = item.estado
    item.estado = nuevoEstado
    error = ''
    transicionar(item, anterior, nuevoEstado)
  }

  // La interfaz es optimista, pero Django conserva la autoridad sobre la
  // maquina de estados: si una transicion no es valida, la tarjeta regresa.
  async function transicionar(item, anterior, nuevoEstado) {
    const body = new FormData()
    body.append('estado', nuevoEstado)
    body.append('csrfmiddlewaretoken', csrf)

    try {
      const res = await fetch(item.update_url, {
        method: 'POST', body, redirect: 'follow',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      })
      if (!res.ok) {
        item.estado = anterior
        error = `No se pudo mover "${item.cliente}" a esa etapa.`
      }
    } catch {
      item.estado = anterior
      error = 'No pudimos guardar el cambio. Intenta de nuevo.'
    }
  }
</script>

{#if error}
  <p class="err cot-tablero__error">{error}</p>
{/if}

<section class="cot-resumen" aria-label="Resumen del tablero">
  <div class="cot-resumen__item">
    <span class="cot-resumen__label">Conversaciones por atender</span>
    <strong>{mensajesNuevos.length}</strong>
    <span class="cot-resumen__hint">WhatsApp sin cotización</span>
  </div>
  <div class="cot-resumen__item">
    <span class="cot-resumen__label">Oportunidades activas</span>
    <strong>{totalActivas}</strong>
    <span class="cot-resumen__hint">En seguimiento</span>
  </div>
  <div class="cot-resumen__help">
    <span class="cot-resumen__help-icon" aria-hidden="true">↔</span>
    Arrastra una cotización a la siguiente etapa cuando avances con el cliente.
  </div>
</section>

<div class="cot-tablero-toolbar">
  <label class="cot-search" aria-label="Buscar en el tablero">
    <span aria-hidden="true">⌕</span>
    <input bind:value={busqueda} type="search" placeholder="Buscar cliente, repuesto o teléfono" />
  </label>
  <button
    type="button"
    class="cot-filter"
    class:cot-filter--activo={soloPendientes}
    onclick={() => soloPendientes = !soloPendientes}
    aria-pressed={soloPendientes}
  >
    <span aria-hidden="true">☷</span> {soloPendientes ? 'Mostrando pendientes' : 'Filtrar pendientes'}
  </button>
</div>

<div class="cot-tablero" aria-label="Pipeline de cotizaciones">
  <section class="cot-columna cot-columna--nuevos" aria-label="Bandeja de WhatsApp">
    <div class="cot-columna__header">
      <div>
        <span class="cot-columna__eyebrow">WhatsApp</span>
        <span class="cot-columna__titulo">Mensajes nuevos</span>
      </div>
      <span class="cot-columna__contador">{mensajesNuevos.length}</span>
    </div>

    <div class="cot-columna__body">
      {#if mensajesNuevos.length === 0}
        <div class="cot-columna__vacio">No tienes mensajes nuevos.</div>
      {/if}

      {#each mensajesNuevos as conv (conv.id)}
        {@const sugerido = clienteSugerido(conv)}
        <article class="cot-tarjeta cot-tarjeta--nuevo">
          <div class="cot-chat-contacto">
            <span class="cot-avatar cot-avatar--wa">{iniciales(conv.nombre)}</span>
            <div>
              <div class="cot-tarjeta__cliente">{conv.nombre || 'Nuevo contacto'}</div>
              <div class="cot-tarjeta__telefono">{conv.telefono}</div>
            </div>
            {#if conv.sinLeer}<span class="cot-unread" aria-label="Mensaje sin leer"></span>{/if}
          </div>
          <p class="cot-tarjeta__producto">{conv.ultimoMensaje}</p>
          <div class="cot-tarjeta__pie">
            <span class="cot-tarjeta__dias">{conv.hora}</span>
            <button type="button" class="cot-link-action" onclick={() => chats.abrir(conv.id)}>
              Abrir chat <span aria-hidden="true">↗</span>
            </button>
          </div>

          {#if creandoDesde === conv.id}
            <form method="post" action={createUrl} class="cot-form-rapido">
              <input type="hidden" name="csrfmiddlewaretoken" value={csrf} />
              <input type="hidden" name="next" value="tablero" />
              <select name="cliente" required aria-label="Cliente para la cotización">
                <option value="">Selecciona el cliente…</option>
                {#each clientes as c (c.id)}
                  <option value={c.id} selected={sugerido?.id === c.id}>{c.nombre} — {c.telefono}</option>
                {/each}
              </select>
              <textarea name="descripcion_repuesto" required placeholder="¿Qué repuesto necesita?">{conv.ultimoMensaje}</textarea>
              <input type="text" name="codigo_producto" placeholder="Código de producto (opcional)" />
              <input type="hidden" name="descuento_pct" value="0" />
              <div class="cot-form-rapido__pie">
                <button type="submit" class="btn">Crear cotización</button>
                <button type="button" class="btn btn--ghost" onclick={() => creandoDesde = null}>Cancelar</button>
              </div>
            </form>
          {:else}
            <button type="button" class="cot-tarjeta__crear" onclick={() => creandoDesde = conv.id}>
              <span aria-hidden="true">+</span> Convertir en cotización
            </button>
          {/if}
        </article>
      {/each}
    </div>
  </section>

  {#each columnas as columna (columna.value)}
    <section
      class="cot-columna cot-columna--{columna.value.toLowerCase()}"
      aria-label={columna.label}
      ondragover={(e) => e.preventDefault()}
      ondrop={() => handleDrop(columna.value)}
    >
      <div class="cot-columna__header">
        <div>
          <span class="cot-columna__eyebrow">Pipeline</span>
          <span class="cot-columna__titulo">{columna.label}</span>
        </div>
        <span class="cot-columna__contador">{columna.items.length}</span>
      </div>

      <div class="cot-columna__body">
        {#if columna.items.length === 0}
          <div class="cot-columna__vacio">Sin cotizaciones en esta etapa.</div>
        {/if}

        {#each columna.items as item (item.id)}
          {@const conv = chats.buscarPorTelefono(item.cliente_telefono)}
          <article class="cot-tarjeta" draggable="true" ondragstart={() => handleDragStart(item)}>
            <div class="cot-tarjeta__encabezado">
              <span class="cot-avatar">{iniciales(item.cliente)}</span>
              <div class="cot-tarjeta__cliente">{item.cliente}</div>
            </div>
            <p class="cot-tarjeta__producto">
              {item.descripcion_repuesto}
              {#if item.codigo_producto}<span class="cot-codigo">{item.codigo_producto}</span>{/if}
            </p>
            <div class="cot-tarjeta__pie">
              <span class="cot-tarjeta__dias">{etiquetaDias(item.dias_desde_actualizacion)}</span>
              {#if conv}
                <button
                  type="button"
                  class="cot-tarjeta__wa"
                  class:cot-tarjeta__wa--sinleer={conv.sinLeer}
                  onclick={() => chats.abrir(conv.id)}
                  aria-label="Abrir chat de WhatsApp de {item.cliente}"
                >⌁</button>
              {/if}
            </div>
          </article>
        {/each}
      </div>
    </section>
  {/each}
</div>

<div class="wa-dock">
  {#each chats.ordenDock as id (id)}
    {@const conv = chats.conversaciones.find(c => c.id === id)}
    {#if conv}
      <ChatFlotante
        conversacion={conv}
        expanded={chats.expandidas.has(id)}
        zIndex={100 + chats.abiertas.indexOf(id)}
        onCerrar={chats.cerrar}
        onEnviar={chats.enviar}
        onEnfocar={chats.enfocar}
      />
    {/if}
  {/each}
</div>
