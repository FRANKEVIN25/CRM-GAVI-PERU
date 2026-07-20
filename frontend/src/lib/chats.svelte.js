// FEAT-07/08: bandeja compartida de WhatsApp -- SOLO mock por ahora.
// La integracion real con Twilio esta pendiente de la verificacion de Meta
// Business Manager, asi que estos datos no vienen de ningun endpoint.
// Este modulo es la unica fuente del mock y de la mecanica de ventanas
// flotantes (abrir/enfocar/cerrar/enviar) -- tanto BandejaWhatsApp.svelte
// como TableroVendedor.svelte lo usan para no duplicar ninguno de los dos.

const MAX_EXPANDIDAS = 3

function conversacionesMock() {
  // "nombre: null" simula un numero que no coincide con ningun Cliente
  // existente ("Desconocido").
  return [
    {
      id: 1, telefono: '+51 999 111 222', nombre: 'Taller Norte',
      ultimoMensaje: '¿Tienen el kit de embrague para Changan?', hora: '10:24', sinLeer: true,
      mensajes: [
        { id: 1, autor: 'cliente', texto: 'Hola, buenas', hora: '10:20' },
        { id: 2, autor: 'cliente', texto: '¿Tienen el kit de embrague para Changan?', hora: '10:24' },
      ],
    },
    {
      id: 2, telefono: '+51 988 222 333', nombre: 'Taller Sur',
      ultimoMensaje: 'Perfecto, paso a recogerlo', hora: '09:58', sinLeer: false,
      mensajes: [
        { id: 1, autor: 'vendedor', texto: 'Su pedido ya está listo', hora: '09:50' },
        { id: 2, autor: 'cliente', texto: 'Perfecto, paso a recogerlo', hora: '09:58' },
      ],
    },
    {
      id: 3, telefono: '+51 977 444 555', nombre: null,
      ultimoMensaje: 'Buenas, vi el anuncio de frenos', hora: '09:12', sinLeer: true,
      mensajes: [
        { id: 1, autor: 'cliente', texto: 'Buenas, vi el anuncio de frenos', hora: '09:12' },
      ],
    },
    {
      id: 4, telefono: '+51 966 777 888', nombre: 'Miguel Cruzado',
      ultimoMensaje: 'Sí, voy a confirmar mañana', hora: 'Ayer', sinLeer: false,
      mensajes: [
        { id: 1, autor: 'vendedor', texto: '¿Confirmamos el pedido de bujías?', hora: 'Ayer' },
        { id: 2, autor: 'cliente', texto: 'Sí, voy a confirmar mañana', hora: 'Ayer' },
      ],
    },
    {
      id: 5, telefono: '+51 955 333 111', nombre: null,
      ultimoMensaje: '¿Hacen envíos a Villa El Salvador?', hora: 'Ayer', sinLeer: true,
      mensajes: [
        { id: 1, autor: 'cliente', texto: '¿Hacen envíos a Villa El Salvador?', hora: 'Ayer' },
      ],
    },
    {
      id: 6, telefono: '+51 944 222 999', nombre: 'Rossy Huamani',
      ultimoMensaje: 'Gracias, quedo atenta', hora: 'Lun', sinLeer: false,
      mensajes: [
        { id: 1, autor: 'cliente', texto: '¿Tienen descuento por volumen?', hora: 'Lun' },
        { id: 2, autor: 'vendedor', texto: 'Sí, desde 10 unidades', hora: 'Lun' },
        { id: 3, autor: 'cliente', texto: 'Gracias, quedo atenta', hora: 'Lun' },
      ],
    },
  ]
}

export function iniciales(nombre) {
  if (!nombre) return '?'
  return nombre.trim().split(/\s+/).slice(0, 2).map(p => p[0]).join('').toUpperCase()
}

// Compara solo los ultimos 9 digitos (celular peruano) para que
// "+51 999 111 222" y "999111222" cuenten como el mismo numero.
// Exportada porque TableroVendedor.svelte tambien la necesita para saber
// que conversaciones NO tienen todavia una Cotizacion asociada.
export function normalizarTelefono(telefono) {
  return (telefono || '').replace(/\D/g, '').slice(-9)
}

// Un solo controlador por pagina montada (Bandeja o Tablero) -- no hay
// runtime compartido entre paginas distintas en esta app multi-pagina,
// asi que cada mount arma su propia copia del mock via esta factory,
// reutilizando siempre la misma logica y el mismo ChatFlotante.svelte.
export function crearControladorChats() {
  let conversaciones = $state(conversacionesMock())
  let abiertas = $state([]) // orden de apertura -- el ultimo id es el mas reciente/enfocado

  let expandidas = $derived(new Set(abiertas.slice(-MAX_EXPANDIDAS)))
  let ordenDock = $derived([...abiertas].reverse())

  function buscarPorTelefono(telefono) {
    const buscado = normalizarTelefono(telefono)
    if (!buscado) return undefined
    return conversaciones.find(c => normalizarTelefono(c.telefono) === buscado)
  }

  function abrir(id) {
    if (abiertas.includes(id)) {
      enfocar(id)
      return
    }
    abiertas = [...abiertas, id]
    const conv = conversaciones.find(c => c.id === id)
    if (conv) conv.sinLeer = false
  }

  function enfocar(id) {
    abiertas = [...abiertas.filter(x => x !== id), id]
    const conv = conversaciones.find(c => c.id === id)
    if (conv) conv.sinLeer = false
  }

  function cerrar(id) {
    abiertas = abiertas.filter(x => x !== id)
  }

  function enviar(id, texto) {
    const conv = conversaciones.find(c => c.id === id)
    if (!conv) return
    const hora = new Date().toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit' })
    conv.mensajes.push({ id: Date.now(), autor: 'vendedor', texto, hora })
    conv.ultimoMensaje = texto
    conv.hora = hora
  }

  return {
    get conversaciones() { return conversaciones },
    get abiertas() { return abiertas },
    get expandidas() { return expandidas },
    get ordenDock() { return ordenDock },
    buscarPorTelefono,
    abrir,
    enfocar,
    cerrar,
    enviar,
  }
}
