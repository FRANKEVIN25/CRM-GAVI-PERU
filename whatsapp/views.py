from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt

from .services import actualizar_estado_twilio, recibir_mensaje_twilio
from .twilio import validar_firma


def _url_firmada(request):
    if settings.TWILIO_WEBHOOK_BASE_URL:
        return settings.TWILIO_WEBHOOK_BASE_URL + request.get_full_path()
    return request.build_absolute_uri()


def _webhook_valido(request):
    return validar_firma(
        url=_url_firmada(request), parametros=request.POST.dict(),
        firma=request.headers.get("X-Twilio-Signature", ""),
    )


@csrf_exempt
def twilio_entrante(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if not _webhook_valido(request):
        return HttpResponseForbidden("Firma Twilio invalida.")
    try:
        recibir_mensaje_twilio(request.POST.dict())
    except ValueError as error:
        return HttpResponseBadRequest(str(error))
    return HttpResponse("<Response></Response>", content_type="text/xml")


@csrf_exempt
def twilio_estado(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if not _webhook_valido(request):
        return HttpResponseForbidden("Firma Twilio invalida.")
    actualizar_estado_twilio(request.POST.dict())
    return HttpResponse(status=204)
