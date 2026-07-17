<script>
  let { addUrl, csrf, username } = $props()

  const CANALES = [
    { value: 'WHATSAPP',  label: 'WhatsApp' },
    { value: 'LLAMADA',   label: 'Llamada' },
    { value: 'MOSTRADOR', label: 'Mostrador' },
  ]
  const CANAL_LABEL = Object.fromEntries(CANALES.map(c => [c.value, c.label]))

  let canal   = $state('')
  let nota    = $state('')
  let loading = $state(false)
  let error   = $state('')

  async function handleSubmit(e) {
    e.preventDefault()
    if (!canal || !nota.trim()) {
      error = 'Selecciona un canal e ingresa una nota.'
      return
    }
    loading = true
    error   = ''

    const body = new FormData()
    body.append('canal', canal)
    body.append('nota', nota.trim())
    body.append('csrfmiddlewaretoken', csrf)

    try {
      const res = await fetch(addUrl, {
        method:   'POST',
        body,
        redirect: 'follow',
        headers:  { 'X-Requested-With': 'XMLHttpRequest' },
      })

      if (res.ok) {
        // Actualización optimista: la Timeline recibe el evento y muestra
        // la nueva interacción de inmediato sin esperar una recarga.
        const nueva = {
          id:           Date.now(),
          canal,
          canal_display: CANAL_LABEL[canal],
          nota:         nota.trim(),
          fecha:        new Date().toLocaleString('es-PE', {
            day: '2-digit', month: '2-digit', year: 'numeric',
            hour: '2-digit', minute: '2-digit',
          }),
          usuario: username,
        }
        document.dispatchEvent(new CustomEvent('interaccion-added', { detail: nueva }))
        canal = ''
        nota  = ''
      } else {
        error = 'No se pudo guardar la interacción. Intenta de nuevo.'
      }
    } catch {
      error = 'Error de conexión. Intenta de nuevo.'
    } finally {
      loading = false
    }
  }
</script>

<div class="add-int">
  <p class="lbl">Registrar interacción</p>

  {#if error}
    <p class="err">{error}</p>
  {/if}

  <form onsubmit={handleSubmit}>
    <div class="row">
      <div class="field canal-field">
        <label for="svelte-canal">Canal</label>
        <select id="svelte-canal" bind:value={canal} required>
          <option value="">Seleccionar...</option>
          {#each CANALES as c}
            <option value={c.value}>{c.label}</option>
          {/each}
        </select>
      </div>

      <div class="field nota-field">
        <label for="svelte-nota">Nota</label>
        <input
          id="svelte-nota"
          type="text"
          bind:value={nota}
          maxlength="280"
          placeholder="¿Qué pasó en este contacto?"
          required
        />
      </div>

      <div class="field submit-field">
        <button type="submit" class="btn" disabled={loading}>
          {loading ? 'Guardando…' : 'Guardar'}
        </button>
      </div>
    </div>
  </form>
</div>

<style>
  .add-int {
    background: #F0EBE2;
    border: 1.5px dashed #DDD5C8;
    border-radius: 10px;
    padding: 20px;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  }

  .lbl {
    font-size: .7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .08em;
    color: #5C4E43;
    margin-bottom: 14px;
  }

  .err {
    font-size: .82rem;
    color: #DC2626;
    padding: 8px 12px;
    background: #FEF2F2;
    border: 1px solid #FECACA;
    border-radius: 6px;
    margin-bottom: 12px;
  }

  .row {
    display: flex;
    gap: 10px;
    align-items: flex-end;
    flex-wrap: wrap;
  }

  .field { display: flex; flex-direction: column; gap: 5px; flex: 1; min-width: 120px; }
  .canal-field  { flex: 0 0 180px; }
  .submit-field { flex: 0; justify-content: flex-end; }

  label {
    font-size: .75rem;
    font-weight: 700;
    color: #5C4E43;
    text-transform: uppercase;
    letter-spacing: .07em;
  }

  select,
  input[type="text"] {
    display: block;
    width: 100%;
    padding: 10px 14px;
    border: 1.5px solid #DDD5C8;
    border-radius: 6px;
    font-family: inherit;
    font-size: .95rem;
    color: #1A1614;
    background: #FFFFFF;
    outline: none;
    -webkit-appearance: none;
    appearance: none;
    transition: border-color .15s, box-shadow .15s;
  }

  select {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%239A8C82' stroke-width='1.5' stroke-linecap='round' fill='none'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 12px center;
    padding-right: 36px;
  }

  select:focus,
  input[type="text"]:focus {
    border-color: #D97B3A;
    box-shadow: 0 0 0 3px rgba(217,123,58,.14);
  }

  .btn {
    display: inline-flex;
    align-items: center;
    padding: 10px 20px;
    background: #D97B3A;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    font-family: inherit;
    font-size: .88rem;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
    transition: background .15s, transform .1s;
  }
  .btn:hover:not(:disabled) { background: #C06929; transform: translateY(-1px); }
  .btn:active:not(:disabled) { transform: none; }
  .btn:disabled { opacity: .6; cursor: not-allowed; }

  @media (max-width: 600px) {
    .row { flex-direction: column; }
    .canal-field { flex: 1; }
  }
</style>
