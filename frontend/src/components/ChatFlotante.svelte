<script>
  // Ventana de chat flotante individual -- mecanica tipo Messenger.
  // Los mensajes viven en `conversacion` (objeto compartido con
  // BandejaWhatsApp.svelte), asi que enviar aca tambien actualiza el
  // "ultimo mensaje" que se ve en la bandeja, sin backend real todavia.
  let { conversacion, expanded, zIndex, onCerrar, onEnviar, onEnfocar } = $props()

  let texto = $state('')
  let bodyEl = $state()
  let posOverride = $state(null) // {left, top} en px mientras se arrastra o luego de soltar

  let dragStart = null
  let moved = false

  function iniciales(nombre) {
    if (!nombre) return '?'
    return nombre.trim().split(/\s+/).slice(0, 2).map(p => p[0]).join('').toUpperCase()
  }

  function handlePointerDown(e) {
    const rect = e.currentTarget.closest('.wa-chat').getBoundingClientRect()
    dragStart = { x: e.clientX, y: e.clientY, left: rect.left, top: rect.top }
    moved = false
    window.addEventListener('pointermove', handlePointerMove)
    window.addEventListener('pointerup', handlePointerUp)
  }

  function handlePointerMove(e) {
    if (!dragStart) return
    const dx = e.clientX - dragStart.x
    const dy = e.clientY - dragStart.y
    if (Math.abs(dx) > 4 || Math.abs(dy) > 4) moved = true
    if (moved) posOverride = { left: dragStart.left + dx, top: dragStart.top + dy }
  }

  function handlePointerUp() {
    window.removeEventListener('pointermove', handlePointerMove)
    window.removeEventListener('pointerup', handlePointerUp)
    if (!moved) onEnfocar(conversacion.id)
    dragStart = null
    moved = false
  }

  function handleSubmit(e) {
    e.preventDefault()
    if (!texto.trim()) return
    onEnviar(conversacion.id, texto.trim())
    texto = ''
  }

  $effect(() => {
    conversacion.mensajes.length
    if (bodyEl) bodyEl.scrollTop = bodyEl.scrollHeight
  })
</script>

<div
  class="wa-chat"
  class:wa-chat--collapsed={!expanded}
  style:z-index={zIndex}
  style:position={posOverride ? 'fixed' : null}
  style:left={posOverride ? posOverride.left + 'px' : null}
  style:top={posOverride ? posOverride.top + 'px' : null}
>
  <div
    class="wa-chat-header"
    role="button"
    tabindex="0"
    onpointerdown={handlePointerDown}
    onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onEnfocar(conversacion.id) } }}
  >
    <div class="wa-chat-header__info">
      <span class="wa-chat-header__avatar">{iniciales(conversacion.nombre)}</span>
      <span class="wa-chat-header__nombre">{conversacion.nombre ?? 'Desconocido'}</span>
    </div>
    <button
      type="button"
      class="wa-chat-header__cerrar"
      onclick={(e) => { e.stopPropagation(); onCerrar(conversacion.id) }}
      aria-label="Cerrar chat"
    >×</button>
  </div>

  {#if expanded}
    <div class="wa-chat-body" bind:this={bodyEl}>
      {#each conversacion.mensajes as msg (msg.id)}
        <div class="wa-msg wa-msg--{msg.autor}">
          {msg.texto}
          <span class="wa-msg__hora">{msg.hora}</span>
        </div>
      {/each}
    </div>
    <form class="wa-chat-footer" onsubmit={handleSubmit}>
      <input class="wa-chat-input" type="text" bind:value={texto} placeholder="Escribe un mensaje…" />
      <button type="submit" class="btn wa-chat-enviar">Enviar</button>
    </form>
  {/if}
</div>
