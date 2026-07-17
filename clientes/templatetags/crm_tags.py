import json
from pathlib import Path

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()

_DIST_REL   = Path('clientes') / 'static' / 'clientes' / 'dist'
_STATIC_URL = '/static/clientes/dist/'


def _manifest_path():
    return Path(settings.BASE_DIR) / _DIST_REL / 'manifest.json'


@register.simple_tag
def interacciones_data_script(queryset):
    """
    Serializa las interacciones del cliente a JSON y las embebe en un
    <script type="application/json"> para que main.js las pueda leer
    sin hacer una petición adicional al servidor.
    """
    data = [
        {
            'id':           i.id,
            'canal':        i.canal,
            'canal_display': i.get_canal_display(),
            'nota':         i.nota,
            'fecha':        i.fecha.strftime('%d/%m/%Y %H:%M'),
            'usuario':      str(i.usuario),
        }
        for i in queryset
    ]
    # ensure_ascii=False preserva ñ/acentos tal cual en el HTML (UTF-8).
    # Reemplazamos '</' para que una nota con '</script>' no rompa el tag.
    json_str = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
    return mark_safe(
        f'<script type="application/json" id="interacciones-data">{json_str}</script>'
    )


@register.simple_tag
def vite_tags(entry_path):
    """
    En desarrollo (sin manifest): carga desde el servidor de Vite en
    localhost:5173 — los cambios en .svelte se reflejan al recargar la página.

    En producción (manifest.json presente tras `npm run build`): inyecta
    el bundle con hash y cualquier hoja de estilos extraída.
    """
    manifest = _manifest_path()
    if manifest.exists():
        with open(manifest, encoding='utf-8') as f:
            data = json.load(f)
        entry = data.get(entry_path, {})
        js    = entry.get('file', '')
        tags  = [f'<script type="module" src="{_STATIC_URL}{js}"></script>']
        for css in entry.get('css', []):
            tags.append(f'<link rel="stylesheet" href="{_STATIC_URL}{css}">')
        return mark_safe('\n  '.join(tags))

    # Fallback: Vite dev server (requiere `npm run dev` corriendo)
    return mark_safe(
        '<script type="module" src="http://localhost:5173/@vite/client"></script>\n'
        f'  <script type="module" src="http://localhost:5173/{entry_path}"></script>'
    )
