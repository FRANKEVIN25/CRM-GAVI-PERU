<script>
  let { cotizaciones, csrf } = $props()

  // Estado local inicializado con lo que Django serializó en el HTML
  let items = $state([...cotizaciones])
  let enCurso = $state(new Set())

  const ESTADO = {
    ENVIADA:    { label: 'Enviada',    border: '#F59E0B', bg: '#FEF3C7', color: '#92400E' },
    CONFIRMADA: { label: 'Confirmada', border: '#3B82F6', bg: '#DBEAFE', color: '#1E40AF' },
    CONVERTIDA: { label: 'Convertida', border: '#22C55E', bg: '#DCFCE7', color: '#166534' },
    PERDIDA:    { label: 'Perdida',    border: '#EF4444', bg: '#FEE2E2', color: '#991B1B' },
  }

  // Misma maquina de estados que Cotizacion.TRANSICIONES en el backend --
  // se duplica aca (igual que CANAL_LABEL en InteraccionForm.svelte) solo
  // para poder calcular los siguientes botones sin otra vuelta al servidor;
  // la validacion real vive en el modelo, esto es puramente cosmetico.
  const TRANSICIONES = {
    ENVIADA:    ['CONFIRMADA', 'PERDIDA'],
    CONFIRMADA: ['CONVERTIDA', 'PERDIDA'],
    CONVERTIDA: [],
    PERDIDA:    [],
  }

  function siguientes(estado) {
    return (TRANSICIONES[estado] ?? []).map(value => ({ value, label: ESTADO[value].label }))
  }

  async function transicionar(item, nuevoEstado) {
    enCurso = new Set(enCurso).add(item.id)

    const body = new FormData()
    body.append('estado', nuevoEstado)
    body.append('csrfmiddlewaretoken', csrf)

    try {
      const res = await fetch(item.update_url, {
        method:   'POST',
        body,
        redirect: 'follow',
        headers:  { 'X-Requested-With': 'XMLHttpRequest' },
      })
      if (res.ok) {
        items = items.map(i => i.id === item.id
          ? { ...i, estado: nuevoEstado, estado_display: ESTADO[nuevoEstado].label, siguientes_estados: siguientes(nuevoEstado) }
          : i)
      }
    } finally {
      const restante = new Set(enCurso)
      restante.delete(item.id)
      enCurso = restante
    }
  }
</script>

<div class="cot-list">
  {#if items.length === 0}
    <div class="cot-empty">Sin cotizaciones registradas.</div>
  {/if}

  {#each items as item (item.id)}
    <div class="cot-card" style:border-left-color={ESTADO[item.estado]?.border}>
      <div class="cot-hd">
        <span class="cot-cliente">{item.cliente}</span>
        <span
          class="cot-estado"
          style:background={ESTADO[item.estado]?.bg}
          style:color={ESTADO[item.estado]?.color}
        >{item.estado_display}</span>
      </div>

      <div class="cot-repuesto">
        {item.descripcion_repuesto}
        {#if item.codigo_producto}<span class="cot-codigo">({item.codigo_producto})</span>{/if}
      </div>

      <div class="cot-meta">
        <span>{item.usuario}</span>
        <span>{item.fecha}</span>
        <span>Desc. {item.descuento_pct}%</span>
      </div>

      {#if item.siguientes_estados.length > 0}
        <div class="cot-acciones">
          {#each item.siguientes_estados as opcion (opcion.value)}
            <button
              type="button"
              class="cot-btn"
              disabled={enCurso.has(item.id)}
              onclick={() => transicionar(item, opcion.value)}
            >Marcar {opcion.label}</button>
          {/each}
        </div>
      {/if}
    </div>
  {/each}
</div>

<style>
  .cot-list { display: flex; flex-direction: column; gap: 8px; }

  .cot-empty {
    padding: 36px 24px;
    text-align: center;
    color: #9A8C82;
    font-size: .88rem;
    border: 1.5px dashed #DDD5C8;
    border-radius: 10px;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  }

  .cot-card {
    border: 1px solid #DDD5C8;
    border-left-width: 4px;
    border-radius: 10px;
    background: #FFFFFF;
    padding: 14px 16px;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    transition: box-shadow .15s;
  }
  .cot-card:hover {
    box-shadow: 0 1px 3px rgba(26,22,20,.08), 0 4px 16px rgba(26,22,20,.05);
  }

  .cot-hd { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 8px; }

  .cot-cliente { font-weight: 700; color: #1A1614; }

  .cot-estado {
    display: inline-block;
    font-size: .68rem;
    font-weight: 700;
    padding: 3px 9px;
    border-radius: 20px;
    text-transform: uppercase;
    letter-spacing: .06em;
    white-space: nowrap;
  }

  .cot-repuesto {
    font-size: .93rem;
    color: #1A1614;
    line-height: 1.55;
    margin-bottom: 8px;
  }
  .cot-codigo { color: #9A8C82; margin-left: 4px; }

  .cot-meta {
    font-size: .76rem;
    color: #9A8C82;
    display: flex;
    gap: 14px;
    flex-wrap: wrap;
  }

  .cot-acciones {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-top: 12px;
  }

  .cot-btn {
    padding: 7px 14px;
    background: #D97B3A;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    font-family: inherit;
    font-size: .8rem;
    font-weight: 600;
    cursor: pointer;
    transition: background .15s, transform .1s;
  }
  .cot-btn:hover:not(:disabled) { background: #C06929; transform: translateY(-1px); }
  .cot-btn:active:not(:disabled) { transform: none; }
  .cot-btn:disabled { opacity: .6; cursor: not-allowed; }
</style>
