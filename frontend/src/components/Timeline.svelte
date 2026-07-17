<script>
  import { onMount } from 'svelte'

  let { interacciones } = $props()

  // Estado local inicializado con los datos que Django serializó en el HTML
  let items = $state([...interacciones])

  const CANAL = {
    WHATSAPP:  { label: 'WhatsApp', border: '#22C55E', bg: '#DCFCE7', color: '#166534' },
    LLAMADA:   { label: 'Llamada',  border: '#3B82F6', bg: '#DBEAFE', color: '#1E40AF' },
    MOSTRADOR: { label: 'Mostrador',border: '#D97B3A', bg: '#FEF3C7', color: '#92400E' },
  }

  function meta(canal) {
    return CANAL[canal] ?? CANAL.MOSTRADOR
  }

  onMount(() => {
    // InteraccionForm despacha este evento al guardar; actualizamos sin recargar
    function handler(e) {
      items = [e.detail, ...items]
    }
    document.addEventListener('interaccion-added', handler)
    return () => document.removeEventListener('interaccion-added', handler)
  })
</script>

<div class="timeline">
  {#if items.length === 0}
    <div class="tl-empty">Sin interacciones registradas.</div>
  {/if}

  {#each items as item (item.id)}
    <div class="interaction" style:border-left-color={meta(item.canal).border}>
      <div class="int-hd">
        <span
          class="channel"
          style:background={meta(item.canal).bg}
          style:color={meta(item.canal).color}
        >{meta(item.canal).label}</span>
      </div>
      <div class="int-note">{item.nota}</div>
      <div class="int-meta">
        <span>{item.fecha}</span>
        <span>{item.usuario}</span>
      </div>
    </div>
  {/each}
</div>

<style>
  .timeline { display: flex; flex-direction: column; gap: 8px; }

  .tl-empty {
    padding: 36px 24px;
    text-align: center;
    color: #9A8C82;
    font-size: .88rem;
    border: 1.5px dashed #DDD5C8;
    border-radius: 10px;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  }

  .interaction {
    border: 1px solid #DDD5C8;
    border-left-width: 4px;
    border-radius: 10px;
    background: #FFFFFF;
    padding: 14px 16px;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    transition: box-shadow .15s;
  }
  .interaction:hover {
    box-shadow: 0 1px 3px rgba(26,22,20,.08), 0 4px 16px rgba(26,22,20,.05);
  }

  .int-hd { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }

  .channel {
    display: inline-block;
    font-size: .68rem;
    font-weight: 700;
    padding: 3px 9px;
    border-radius: 20px;
    text-transform: uppercase;
    letter-spacing: .06em;
  }

  .int-note {
    font-size: .93rem;
    color: #1A1614;
    line-height: 1.55;
    margin-bottom: 8px;
  }

  .int-meta {
    font-size: .76rem;
    color: #9A8C82;
    display: flex;
    gap: 14px;
  }
</style>
